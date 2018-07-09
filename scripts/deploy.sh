    #!/bin/bash

# nicked from here https://github.com/18F/cf-cd-example/blob/master/deploy.sh

set -e

unamestr=`uname`

if ! hash cf 2>/dev/null; then
  echo "Installing Cloud Foundry CLI..."
  if [[ "$unamestr" == 'Darwin' ]]; then
    brew tap cloudfoundry/tap
    brew install cf-cli
  else
    mkdir -p tmp
    PATH=$PWD/tmp:$PATH
    curl -L "https://cli.run.pivotal.io/stable?release=linux64-binary&source=github" | tar -zx -C tmp
  fi
fi


if [ -n "$CF_USERNAME" ] && [ -n "$CF_PASSWORD" ]; then
  cf login -a "$CF_API" -u "$CF_USERNAME" -p "$CF_PASSWORD" -o "$CF_ORGANIZATION" -s "$CF_SPACE"
fi

# push default manifest - i.e. the actual application
#cf push

# zero downtime push with autopilot
cf install-plugin autopilot -f -r CF-Community
cf zero-downtime-push brownfield-sites-validator -f manifest.yml
