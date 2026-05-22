#!/usr/bin/env bash
set -e

echo "Configuring git hooks..."
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit

# -------------------------------------------------------
# Bootstrap local .env and cert files from *.example
# -------------------------------------------------------
echo ""
echo "Bootstrapping local config files from *.example templates..."

bootstrap() {
    local example="$1"
    local target="${example%.example}"
    if [ ! -f "$target" ]; then
        cp "$example" "$target"
        echo "  Created: $target"
    else
        echo "  Skipped: $target already exists"
    fi
}

while IFS= read -r -d '' f; do
    bootstrap "$f"
done < <(find . -type f \( -name '*.env.example' -o -name 'certfile.crt.example' -o -name 'keyfile.key.example' \) -not -path './.git/*' -print0)

# -------------------------------------------------------
# Prompt for all <CHANGEME> values in local .env files
# -------------------------------------------------------
echo ""
echo "Searching for values that need to be configured..."
echo "Press Enter to keep the current placeholder, or type a new value."
echo ""

while IFS=: read -r file lineno rest; do
    # Skip pure comment lines
    [[ "$rest" =~ ^[[:space:]]*# ]] && continue

    if [[ "$rest" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)[[:space:]]+#+[[:space:]]*\<CHANGEME\> ]]; then
        # env format: KEY=value # <CHANGEME>
        key="${BASH_REMATCH[1]}"
        current="${BASH_REMATCH[2]}"

        echo "[$file]  $key"
        echo "  Current value: $current"
        printf "  New value (Enter to skip): "
        read -r newval </dev/tty

        if [ -n "$newval" ]; then
            sed -i "s|^${key}=.*|${key}=${newval}|" "$file"
            echo "  -> Updated."
        fi
        echo ""
    elif [[ "$rest" =~ ^([[:space:]]*)([A-Za-z_][A-Za-z0-9_]*):[[:space:]]+([^#]+)[[:space:]]*#.*\<CHANGEME\> ]]; then
        # yaml format:   key: value # <CHANGEME>
        indent="${BASH_REMATCH[1]}"
        key="${BASH_REMATCH[2]}"
        current="${BASH_REMATCH[3]%"${BASH_REMATCH[3]##*[! ]}"}"  # trim trailing whitespace

        echo "[$file]  $key"
        echo "  Current value: $current"
        printf "  New value (Enter to skip): "
        read -r newval </dev/tty

        if [ -n "$newval" ]; then
            sed -i "s|^${indent}${key}:.*|${indent}${key}: ${newval}|" "$file"
            echo "  -> Updated."
        fi
        echo ""
    fi
done < <(grep -rn '<CHANGEME>' . \
    --include='*.env' \
    --include='*.yaml' \
    --include='*.yml' \
    --exclude='*.example' \
    --exclude-dir='.git')

# -------------------------------------------------------

echo "Done. Next steps:"
echo "  1. Replace modules/core/certs/certfile.crt and keyfile.key with real TLS files"
echo "  2. docker compose up -d"
