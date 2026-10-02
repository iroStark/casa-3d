#!/bin/zsh
# Publica web/dist no branch gh-pages (GitHub Pages) sem misturar com o código-fonte.
set -e
cd "$(dirname "$0")/.."
TMP=$(mktemp -d)
cp -R web/dist/. "$TMP/"
touch "$TMP/.nojekyll"
cd "$TMP"
git init -q -b gh-pages
git add -A
git commit -q -m "Publicação do site $(date +%Y-%m-%d\ %H:%M)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push -q -f https://github.com/iroStark/casa-3d.git gh-pages
echo "PUBLICADO"
