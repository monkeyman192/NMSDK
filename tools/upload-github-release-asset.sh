#!/usr/bin/env bash
#
# Author: Stefan Buck
# License: MIT
# https://gist.github.com/stefanbuck/ce788fee19ab6eb0b4447a85fc99f447
#
# Contains modifications suggested by huxingyi:
# https://gist.github.com/stefanbuck/ce788fee19ab6eb0b4447a85fc99f447#gistcomment-2555516
# as well as personal changes (by monkeyman192).
#
# This script accepts the following parameters:
#
# * owner
# * repo
# * filename
# * github_api_token
#
# Script to upload a release asset using the GitHub API v3.
#
# Example:
#
# upload-github-release-asset.sh github_api_token=TOKEN owner=stefanbuck repo=playground filename=./build.zip
#

# Check dependencies.
set -e
xargs=$(which gxargs || which xargs)

# Validate settings.
[ "$TRACE" ] && set -x

CONFIG=$@

for line in $CONFIG; do
  eval "$line"
done

# Get the version of the plugin
tag=$(bash ./tools/read_nmsdk_version.sh)

# Define variables.
GH_API="https://api.github.com"
GH_REPO="$GH_API/repos/$owner/$repo"
GH_TAGS="$GH_REPO/releases/tags/$tag"
AUTH="Authorization: token $github_api_token"
WGET_ARGS="--content-disposition --auth-no-challenge --no-cookie"
CURL_ARGS="-LJO#"

if [[ "$tag" == 'LATEST' ]]; then
  GH_TAGS="$GH_REPO/releases/latest"
fi

# Validate token.
curl -o /dev/null -sH "$AUTH" $GH_REPO || { echo "Error: Invalid repo, token or network issue!";  exit 1; }

# Read asset tags.
response=$(curl -sH "$AUTH" $GH_TAGS)

# Get ID of the release.
eval $(echo "$response" | grep -m 1 "id.:" | grep -w id | tr : = | tr -cd '[[:alnum:]]=')

if [[ "$id" == '' ]]; then
    # Create a release automatically
    curl \
        --user $owner:$github_api_token \
        --header "Accept: application/vnd.github.manifold-preview" \
        --data "{\"tag_name\":\"$tag\"}" \
        "https://api.github.com/repos/$owner/$repo/releases?access_token=$github_api_token"

    # Then re-ask for the ID
    response=$(curl -sH "$AUTH" $GH_TAGS)
    eval $(echo "$response" | grep -m 1 "id.:" | grep -w id | tr : = | tr -cd '[[:alnum:]]=')
fi
release_id="$id"

# Get ID of the asset based on given filename.
id=""
eval $(echo "$response" | grep -C1 "name.:.\+$filename" | grep -m 1 "id.:" | grep -w id | tr : = | tr -cd '[[:alnum:]]=')
asset_id="$id"
if [ "$asset_id" = "" ]; then
    echo "No need to overwrite asset"
else
    echo "Deleting asset($asset_id)... "
    curl "$GITHUB_OAUTH_BASIC" -X "DELETE" -H "Authorization: token $github_api_token" "https://api.github.com/repos/$owner/$repo/releases/assets/$asset_id"
fi

# Upload asset
echo "Uploading asset... "

# Construct url
GH_ASSET="https://uploads.github.com/repos/$owner/$repo/releases/$release_id/assets?name=$(basename $filename)"

curl "$GITHUB_OAUTH_BASIC" --data-binary @"$filename" -H "Authorization: token $github_api_token" -H "Content-Type: application/octet-stream" $GH_ASSET
