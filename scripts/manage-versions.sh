#!/bin/bash

# Truffaldino Version Management
# RCS-style versioning for configuration files

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VERSION_DIR="$HOME/.truffaldino/versions"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  list [FILE]       List versions of a file (or all files)"
    echo "  show FILE VERSION Show specific version content"
    echo "  diff FILE V1 V2   Compare two versions"
    echo "  restore FILE VER  Restore a file to a specific version"
    echo "  cleanup [DAYS]    Remove versions older than DAYS (default: 30)"
    echo "  info             Show version directory info"
    echo ""
    echo "Examples:"
    echo "  $0 list"
    echo "  $0 list master-config.yaml"
    echo "  $0 show master-config.yaml 20240130_143022"
    echo "  $0 restore claude_desktop_config.json 20240130_143022"
    echo "  $0 cleanup 7"
}

list_versions() {
    local file_pattern="$1"
    
    echo -e "${BLUE}📁 Version Directory: ${VERSION_DIR}${NC}"
    echo ""
    
    if [ ! -d "$VERSION_DIR" ]; then
        echo -e "${YELLOW}⚠️  No versions directory found${NC}"
        return
    fi
    
    if [ -n "$file_pattern" ]; then
        versions=$(find "$VERSION_DIR" -name "${file_pattern}.*" -type f | sort)
    else
        versions=$(find "$VERSION_DIR" -type f | sort)
    fi
    
    if [ -z "$versions" ]; then
        echo -e "${YELLOW}No versions found${NC}"
        return
    fi
    
    current_file=""
    while IFS= read -r version_file; do
        if [ -z "$version_file" ]; then continue; fi
        
        filename=$(basename "$version_file")
        base_file=$(echo "$filename" | cut -d'.' -f1-2)  # Get file.ext part
        timestamp=$(echo "$filename" | cut -d'.' -f3-)    # Get timestamp part
        
        if [ "$base_file" != "$current_file" ]; then
            if [ -n "$current_file" ]; then echo ""; fi
            echo -e "${GREEN}📄 $base_file${NC}"
            current_file="$base_file"
        fi
        
        # Format timestamp for display
        if [[ $timestamp =~ ^([0-9]{8})_([0-9]{6})$ ]]; then
            date_part=${BASH_REMATCH[1]}
            time_part=${BASH_REMATCH[2]}
            formatted_date="${date_part:0:4}-${date_part:4:2}-${date_part:6:2}"
            formatted_time="${time_part:0:2}:${time_part:2:2}:${time_part:4:2}"
            display_time="$formatted_date $formatted_time"
        else
            display_time="$timestamp"
        fi
        
        file_size=$(ls -lh "$version_file" | awk '{print $5}')
        echo "   $timestamp  ($display_time)  [$file_size]"
    done <<< "$versions"
}

show_version() {
    local file_name="$1"
    local version="$2"
    
    if [ -z "$file_name" ] || [ -z "$version" ]; then
        echo -e "${RED}❌ Please specify both file name and version${NC}"
        usage
        return 1
    fi
    
    version_file="$VERSION_DIR/${file_name}.${version}"
    
    if [ ! -f "$version_file" ]; then
        echo -e "${RED}❌ Version not found: $version_file${NC}"
        return 1
    fi
    
    echo -e "${BLUE}📄 $file_name version $version${NC}"
    echo -e "${BLUE}$(date -r "$version_file" '+%Y-%m-%d %H:%M:%S')${NC}"
    echo ""
    cat "$version_file"
}

diff_versions() {
    local file_name="$1"
    local version1="$2"
    local version2="$3"
    
    if [ -z "$file_name" ] || [ -z "$version1" ] || [ -z "$version2" ]; then
        echo -e "${RED}❌ Please specify file name and two versions${NC}"
        usage
        return 1
    fi
    
    version_file1="$VERSION_DIR/${file_name}.${version1}"
    version_file2="$VERSION_DIR/${file_name}.${version2}"
    
    if [ ! -f "$version_file1" ]; then
        echo -e "${RED}❌ Version not found: $version_file1${NC}"
        return 1
    fi
    
    if [ ! -f "$version_file2" ]; then
        echo -e "${RED}❌ Version not found: $version_file2${NC}"
        return 1
    fi
    
    echo -e "${BLUE}📊 Comparing $file_name: $version1 vs $version2${NC}"
    echo ""
    
    if command -v colordiff >/dev/null 2>&1; then
        diff -u "$version_file1" "$version_file2" | colordiff
    else
        diff -u "$version_file1" "$version_file2"
    fi
}

restore_version() {
    local file_name="$1"
    local version="$2"
    
    if [ -z "$file_name" ] || [ -z "$version" ]; then
        echo -e "${RED}❌ Please specify both file name and version${NC}"
        usage
        return 1
    fi
    
    version_file="$VERSION_DIR/${file_name}.${version}"
    
    if [ ! -f "$version_file" ]; then
        echo -e "${RED}❌ Version not found: $version_file${NC}"
        return 1
    fi
    
    # Find the current file location
    current_file=""
    if [ -f "$PROJECT_ROOT/configs/$file_name" ]; then
        current_file="$PROJECT_ROOT/configs/$file_name"
    elif [ -f "$PROJECT_ROOT/configs/generated/$file_name" ]; then
        current_file="$PROJECT_ROOT/configs/generated/$file_name"
    else
        echo -e "${YELLOW}⚠️  Current file not found, specify target location:${NC}"
        read -p "Target path: " current_file
        if [ -z "$current_file" ]; then
            echo -e "${RED}❌ No target specified${NC}"
            return 1
        fi
    fi
    
    # Backup current file before restore
    if [ -f "$current_file" ]; then
        timestamp=$(date +"%Y%m%d_%H%M%S")
        backup_file="$VERSION_DIR/${file_name}.backup_${timestamp}"
        cp "$current_file" "$backup_file"
        echo -e "${GREEN}💾 Current file backed up to: $(basename "$backup_file")${NC}"
    fi
    
    # Restore the version
    cp "$version_file" "$current_file"
    echo -e "${GREEN}✅ Restored $file_name to version $version${NC}"
    echo -e "${BLUE}📍 File location: $current_file${NC}"
}

cleanup_versions() {
    local days="${1:-30}"
    
    if [ ! -d "$VERSION_DIR" ]; then
        echo -e "${YELLOW}⚠️  No versions directory found${NC}"
        return
    fi
    
    echo -e "${BLUE}🧹 Cleaning up versions older than $days days${NC}"
    
    old_files=$(find "$VERSION_DIR" -type f -mtime +$days)
    
    if [ -z "$old_files" ]; then
        echo -e "${GREEN}✅ No old versions to clean up${NC}"
        return
    fi
    
    echo "Files to be removed:"
    echo "$old_files" | while read -r file; do
        if [ -n "$file" ]; then
            echo "  $(basename "$file")"
        fi
    done
    
    echo ""
    read -p "Continue? (y/N): " confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        echo "$old_files" | while read -r file; do
            if [ -n "$file" ]; then
                rm "$file"
            fi
        done
        echo -e "${GREEN}✅ Cleanup complete${NC}"
    else
        echo -e "${YELLOW}Cleanup cancelled${NC}"
    fi
}

show_info() {
    echo -e "${BLUE}📊 Truffaldino Version Information${NC}"
    echo ""
    echo -e "${GREEN}Version Directory:${NC} $VERSION_DIR"
    
    if [ ! -d "$VERSION_DIR" ]; then
        echo -e "${YELLOW}⚠️  Directory doesn't exist yet${NC}"
        return
    fi
    
    total_files=$(find "$VERSION_DIR" -type f | wc -l)
    total_size=$(du -sh "$VERSION_DIR" 2>/dev/null | cut -f1)
    
    echo -e "${GREEN}Total Versions:${NC} $total_files"
    echo -e "${GREEN}Total Size:${NC} $total_size"
    echo ""
    
    # Show breakdown by file
    echo -e "${GREEN}Files with versions:${NC}"
    find "$VERSION_DIR" -type f | sed 's/.*\///g' | cut -d'.' -f1-2 | sort | uniq -c | while read count file; do
        echo "  $file: $count versions"
    done
}

# Main command handling
case "${1:-list}" in
    "list")
        list_versions "$2"
        ;;
    "show")
        show_version "$2" "$3"
        ;;
    "diff")
        diff_versions "$2" "$3" "$4"
        ;;
    "restore")
        restore_version "$2" "$3"
        ;;
    "cleanup")
        cleanup_versions "$2"
        ;;
    "info")
        show_info
        ;;
    "help"|"-h"|"--help")
        usage
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo ""
        usage
        exit 1
        ;;
esac