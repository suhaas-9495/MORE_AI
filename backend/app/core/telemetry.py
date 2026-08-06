from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from backend.app.core.config import settings
import os


def setup_telemetry(app=None):
    """
    Initializes OpenTelemetry distributed tracing.
    Every HTTP request, agent call, DB query gets a trace span.
    In production: export to Jaeger, Grafana Tempo, or AWS X-Ray.
    """
    resource = Resource.create({
        "service.name": "moreai-api",
        "service.version": "1.0.0",
        "deployment.environment": settings.env,
    })

    provider = TracerProvider(resource=resource)

    # console exporter for development — see traces in terminal
    if settings.env == "development":
        provider.add_span_processor(
            BatchSpanProcessor(ConsoleSpanExporter())
        )

    # OTLP exporter for production — sends to Jaeger/Grafana
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        provider.add_span_processor(
            BatchSpanProcessor(
                OTLPSpanExporter(endpoint=otlp_endpoint)
            )
        )

    trace.set_tracer_provider(provider)

    # auto-instrument FastAPI — traces every HTTP request automatically
    if app:
        FastAPIInstrumentor.instrument_app(app)

    return trace.get_tracer("moreai")


def get_tracer():
    return trace.get_tracer("moreai")