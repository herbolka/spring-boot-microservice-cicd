#!/bin/bash

# Validate that the application is running
APP_URL="http://<external-ip>:<port>/currency-conversion-service"

# Check if the application is reachable
if curl -s --head "$APP_URL" | grep "200 OK" > /dev/null; then
    echo "Validation successful: Application is running."
else
    echo "Validation failed: Application is not reachable."
    exit 1
fi

# Additional checks can be added here as needed
# For example, checking specific endpoints or response content

echo "Validation completed."