# Task 3

Create a custom image:
- Base Image: `postman/newman:5.3-alpine`
- Update/upgrade the image packages to the latest
- Globally install node modules: `newman-reporter-csvallinone`
- Install extra packages: `curl`, `zip`, `ping`
- Set DNS explicitly `to 8.8.8.8` and `1.1.1.1`
- Remove the installation cache
- Set an environment variable `NODE_PATH` to `/usr/local/lib/node_modules`
- Set working directory to `/etc/newman`
- Set the entry point to `newman`

``` dockerfile
# Use a postman base image
FROM postman/newman:5.3-alpine

USER root

# Update OS Packages
RUN apk update && apk upgrade -y --no-cache

## Install newman-reporter-csvallinone module
# 1. Install dependencies
RUN apk add --no-cache nodejs npm
# 2. Install Newman and the CSV reporter
RUN npm install -g newman newman-reporter-csvallinone
# 3. Remove nmp cache
RUN nmp cache clean --force

# Install curl zip ping
RUN apk add --no-cache curl zip iputils

# Set DNS
RUN echo -e 'nameserver 8.8.8.8\nnameserver 1.1.1.1' > /etc/resolv.conf

# Set Environment Variable
ENV NODE_PATH=/usr/local/lib/node_modules

# Set Working directory
WORKDIR /etc/newman

# Set Entrypoint
ENTRYPOINT ["newman"]
```