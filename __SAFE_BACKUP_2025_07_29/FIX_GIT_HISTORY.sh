#!/bin/bash
# 🚨 KRYTYCZNY FIX - USUWA TOKENY Z HISTORII GIT

echo "🚨 USUWANIE TOKENÓW Z HISTORII GIT..."
echo "⚠️  To NIEODWRACALNIE zmieni historię commitów!"
echo

read -p "Czy chcesz kontynuować? (tak/nie): " confirm
if [ "$confirm" != "tak" ]; then
    echo "❌ Anulowano"
    exit 1
fi

echo "🔄 Tworzę backup przed operacją..."
git tag backup-before-history-cleanup HEAD

echo "🧹 Usuwam pliki z tokenami z całej historii..."

# Usuń konkretny plik z całej historii
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch HOOK_BOOST_3.0/README_RENDER.md' \
  --prune-empty --tag-name-filter cat -- --all

# Wyczyść reflog i garbage collect
echo "🗑️  Czyszczę reflog..."
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo "✅ Historia Git oczyszczona!"
echo "⚠️  MUSISZ zrobić force push na GitHub:"
echo "   git push --force-with-lease origin main"
echo "   git push --force-with-lease origin --all"
echo "   git push --force-with-lease origin --tags"

echo
echo "🔄 Następnie NATYCHMIAST zmień wszystkie tokeny:"
echo "   - Discord Bot Token"
echo "   - YouTube API Key"  
echo "   - GitHub Personal Access Token" 