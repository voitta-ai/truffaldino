#!/usr/bin/env node

import { readFileSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const distPath = join(__dirname, '..', 'dist', 'index.js');

// Add shebang to the built file
const content = readFileSync(distPath, 'utf8');
const contentWithShebang = '#!/usr/bin/env node\n' + content;
writeFileSync(distPath, contentWithShebang);

console.log('✅ Build completed - added shebang to index.js');