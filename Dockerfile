# ============================================================================
# Build Stage
# ============================================================================
FROM maven:3.8.5-openjdk-11 as builder

WORKDIR /build

# Copy source code
COPY . .

# Build application
RUN mvn clean package -DskipTests

# ============================================================================
# Runtime Stage
# ============================================================================
FROM eclipse-temurin:11-jre-focal

# Create app user (non-root for security)
RUN useradd -m appuser

WORKDIR /app

# Copy JAR from builder
COPY --from=builder /build/target/*.jar app.jar

# Change ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/actuator/health || exit 1

# Run application
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
