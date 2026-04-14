# ============================================================================
# Build Stage
# ============================================================================

FROM maven:3.8.5-eclipse-temurin-11 AS builder

WORKDIR /build


COPY pom.xml .


RUN mvn dependency:go-offline -B


COPY src ./src


RUN mvn clean package -DskipTests

# ============================================================================
# Runtime Stage
# ============================================================================
FROM eclipse-temurin:11-jre-focal


RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN useradd -m appuser
WORKDIR /app


COPY --from=builder /build/target/*.jar app.jar
RUN chown -R appuser:appuser /app

USER appuser
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/actuator/health || exit 1

ENTRYPOINT ["java", "-jar", "app.jar"]