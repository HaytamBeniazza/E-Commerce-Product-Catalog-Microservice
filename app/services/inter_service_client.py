"""Inter-service communication client for microservices architecture.

This module provides HTTP clients and event-driven communication
patterns for communicating with other microservices in a
multi-database environment.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import aiohttp
import httpx
from circuitbreaker import circuit
from fastapi import HTTPException, status
from pydantic import BaseModel

from app.config_multi_service import get_multi_service_settings

logger = logging.getLogger(__name__)
settings = get_multi_service_settings()


class ServiceResponse(BaseModel):
    """Standard response model for inter-service communication."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    service: str
    request_id: str


class ServiceEvent(BaseModel):
    """Event model for event-driven communication."""
    event_id: str
    event_type: str
    service: str
    timestamp: float
    data: Dict[str, Any]
    correlation_id: Optional[str] = None


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class BaseServiceClient:
    """Base class for inter-service HTTP communication."""
    
    def __init__(self, service_name: str, base_url: str, timeout: int = 30):
        self.service_name = service_name
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session: Optional[httpx.AsyncClient] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = httpx.AsyncClient(
            timeout=self.timeout,
            headers={
                "User-Agent": f"product-service/{settings.SERVICE_VERSION}",
                "X-Service-Name": settings.SERVICE_NAME,
                "X-Request-ID": str(uuid4()),
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.aclose()
    
    @circuit(
        failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
        recovery_timeout=settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
        expected_exception=httpx.HTTPError
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        auth_token: Optional[str] = None
    ) -> ServiceResponse:
        """Make HTTP request with circuit breaker protection."""
        if not self.session:
            raise RuntimeError("Client session not initialized. Use async context manager.")
        
        url = f"{self.base_url}{endpoint}"
        request_headers = headers or {}
        
        # Add authentication if provided
        if auth_token:
            request_headers["Authorization"] = f"Bearer {auth_token}"
        
        # Add service-to-service authentication
        if settings.ENABLE_SERVICE_AUTH:
            request_headers["X-Service-Token"] = settings.SERVICE_TO_SERVICE_SECRET
        
        request_id = str(uuid4())
        request_headers["X-Request-ID"] = request_id
        
        try:
            logger.info(
                f"Making {method} request to {self.service_name}",
                extra={
                    "service": self.service_name,
                    "method": method,
                    "url": url,
                    "request_id": request_id
                }
            )
            
            response = await self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=request_headers
            )
            
            response.raise_for_status()
            response_data = response.json()
            
            logger.info(
                f"Successful response from {self.service_name}",
                extra={
                    "service": self.service_name,
                    "status_code": response.status_code,
                    "request_id": request_id
                }
            )
            
            return ServiceResponse(
                success=True,
                data=response_data,
                service=self.service_name,
                request_id=request_id
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error from {self.service_name}: {e.response.status_code}",
                extra={
                    "service": self.service_name,
                    "status_code": e.response.status_code,
                    "request_id": request_id,
                    "error": str(e)
                }
            )
            
            return ServiceResponse(
                success=False,
                error=f"HTTP {e.response.status_code}: {e.response.text}",
                service=self.service_name,
                request_id=request_id
            )
            
        except httpx.RequestError as e:
            logger.error(
                f"Request error to {self.service_name}: {str(e)}",
                extra={
                    "service": self.service_name,
                    "request_id": request_id,
                    "error": str(e)
                }
            )
            
            return ServiceResponse(
                success=False,
                error=f"Request failed: {str(e)}",
                service=self.service_name,
                request_id=request_id
            )
        
        except Exception as e:
            logger.error(
                f"Unexpected error communicating with {self.service_name}: {str(e)}",
                extra={
                    "service": self.service_name,
                    "request_id": request_id,
                    "error": str(e)
                }
            )
            
            return ServiceResponse(
                success=False,
                error=f"Unexpected error: {str(e)}",
                service=self.service_name,
                request_id=request_id
            )
    
    async def get(self, endpoint: str, params: Optional[Dict] = None, auth_token: Optional[str] = None) -> ServiceResponse:
        """Make GET request."""
        return await self._make_request("GET", endpoint, params=params, auth_token=auth_token)
    
    async def post(self, endpoint: str, data: Optional[Dict] = None, auth_token: Optional[str] = None) -> ServiceResponse:
        """Make POST request."""
        return await self._make_request("POST", endpoint, data=data, auth_token=auth_token)
    
    async def put(self, endpoint: str, data: Optional[Dict] = None, auth_token: Optional[str] = None) -> ServiceResponse:
        """Make PUT request."""
        return await self._make_request("PUT", endpoint, data=data, auth_token=auth_token)
    
    async def delete(self, endpoint: str, auth_token: Optional[str] = None) -> ServiceResponse:
        """Make DELETE request."""
        return await self._make_request("DELETE", endpoint, auth_token=auth_token)


class UserServiceClient(BaseServiceClient):
    """Client for communicating with User Service."""
    
    def __init__(self):
        super().__init__("user-service", settings.USER_SERVICE_URL)
    
    async def get_user(self, user_id: str, auth_token: str) -> ServiceResponse:
        """Get user by ID."""
        return await self.get(f"/api/v1/users/{user_id}", auth_token=auth_token)
    
    async def validate_user(self, auth_token: str) -> ServiceResponse:
        """Validate user token and get user info."""
        return await self.get("/api/v1/auth/me", auth_token=auth_token)
    
    async def check_user_permissions(self, user_id: str, permission: str, auth_token: str) -> ServiceResponse:
        """Check if user has specific permission."""
        return await self.get(
            f"/api/v1/users/{user_id}/permissions/{permission}",
            auth_token=auth_token
        )


class OrderServiceClient(BaseServiceClient):
    """Client for communicating with Order Service."""
    
    def __init__(self):
        super().__init__("order-service", settings.ORDER_SERVICE_URL)
    
    async def get_product_orders(self, product_id: str, auth_token: str) -> ServiceResponse:
        """Get orders containing specific product."""
        return await self.get(
            f"/api/v1/orders/by-product/{product_id}",
            auth_token=auth_token
        )
    
    async def notify_product_updated(self, product_id: str, changes: Dict, auth_token: str) -> ServiceResponse:
        """Notify order service about product updates."""
        return await self.post(
            f"/api/v1/orders/product-updated/{product_id}",
            data=changes,
            auth_token=auth_token
        )


class InventoryServiceClient(BaseServiceClient):
    """Client for communicating with Inventory Service."""
    
    def __init__(self):
        super().__init__("inventory-service", settings.INVENTORY_SERVICE_URL)
    
    async def get_stock_level(self, product_id: str) -> ServiceResponse:
        """Get current stock level for product."""
        return await self.get(f"/api/v1/inventory/{product_id}/stock")
    
    async def reserve_stock(self, product_id: str, quantity: int, order_id: str, auth_token: str) -> ServiceResponse:
        """Reserve stock for an order."""
        return await self.post(
            f"/api/v1/inventory/{product_id}/reserve",
            data={"quantity": quantity, "order_id": order_id},
            auth_token=auth_token
        )
    
    async def update_stock(self, product_id: str, quantity: int, auth_token: str) -> ServiceResponse:
        """Update stock level."""
        return await self.put(
            f"/api/v1/inventory/{product_id}/stock",
            data={"quantity": quantity},
            auth_token=auth_token
        )


class EventPublisher:
    """Event publisher for event-driven communication."""
    
    def __init__(self):
        self.rabbitmq_url = settings.RABBITMQ_URL
        self.exchange = settings.RABBITMQ_EXCHANGE
        self.connection = None
        self.channel = None
    
    async def connect(self):
        """Connect to RabbitMQ."""
        try:
            import aio_pika
            
            self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()
            
            # Declare exchange
            self.exchange_obj = await self.channel.declare_exchange(
                self.exchange,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            logger.info("Connected to RabbitMQ for event publishing")
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise
    
    async def disconnect(self):
        """Disconnect from RabbitMQ."""
        if self.connection:
            await self.connection.close()
    
    async def publish_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        routing_key: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        """Publish event to message queue."""
        if not settings.ENABLE_EVENT_PUBLISHING:
            logger.debug(f"Event publishing disabled, skipping event: {event_type}")
            return
        
        if not self.channel:
            await self.connect()
        
        event = ServiceEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            service=settings.SERVICE_NAME,
            timestamp=asyncio.get_event_loop().time(),
            data=data,
            correlation_id=correlation_id
        )
        
        routing_key = routing_key or f"product.{event_type}"
        
        try:
            import aio_pika
            
            message = aio_pika.Message(
                json.dumps(event.dict()).encode(),
                headers={
                    "event_type": event_type,
                    "service": settings.SERVICE_NAME,
                    "event_id": event.event_id,
                },
                correlation_id=correlation_id
            )
            
            await self.exchange_obj.publish(
                message,
                routing_key=routing_key
            )
            
            logger.info(
                f"Published event: {event_type}",
                extra={
                    "event_id": event.event_id,
                    "event_type": event_type,
                    "routing_key": routing_key,
                    "correlation_id": correlation_id
                }
            )
            
        except Exception as e:
            logger.error(
                f"Failed to publish event {event_type}: {str(e)}",
                extra={
                    "event_type": event_type,
                    "error": str(e)
                }
            )
            raise


class InterServiceManager:
    """Manager for all inter-service communications."""
    
    def __init__(self):
        self.user_client = UserServiceClient()
        self.order_client = OrderServiceClient()
        self.inventory_client = InventoryServiceClient()
        self.event_publisher = EventPublisher()
    
    async def initialize(self):
        """Initialize all service connections."""
        if settings.ENABLE_EVENT_PUBLISHING:
            await self.event_publisher.connect()
    
    async def cleanup(self):
        """Cleanup all service connections."""
        if settings.ENABLE_EVENT_PUBLISHING:
            await self.event_publisher.disconnect()
    
    async def validate_user_access(self, auth_token: str, required_permission: Optional[str] = None) -> Dict[str, Any]:
        """Validate user and check permissions."""
        async with self.user_client as client:
            # Validate user token
            user_response = await client.validate_user(auth_token)
            
            if not user_response.success:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication token"
                )
            
            user_data = user_response.data
            
            # Check specific permission if required
            if required_permission:
                perm_response = await client.check_user_permissions(
                    user_data["id"],
                    required_permission,
                    auth_token
                )
                
                if not perm_response.success or not perm_response.data.get("has_permission"):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"User lacks required permission: {required_permission}"
                    )
            
            return user_data
    
    async def sync_inventory(self, product_id: str, new_stock: int, auth_token: str) -> bool:
        """Synchronize inventory with inventory service."""
        async with self.inventory_client as client:
            response = await client.update_stock(product_id, new_stock, auth_token)
            return response.success
    
    async def notify_product_created(self, product_data: Dict[str, Any], correlation_id: Optional[str] = None):
        """Notify other services about product creation."""
        await self.event_publisher.publish_event(
            "created",
            product_data,
            correlation_id=correlation_id
        )
    
    async def notify_product_updated(self, product_id: str, changes: Dict[str, Any], correlation_id: Optional[str] = None):
        """Notify other services about product updates."""
        await self.event_publisher.publish_event(
            "updated",
            {"product_id": product_id, "changes": changes},
            correlation_id=correlation_id
        )
    
    async def notify_product_deleted(self, product_id: str, correlation_id: Optional[str] = None):
        """Notify other services about product deletion."""
        await self.event_publisher.publish_event(
            "deleted",
            {"product_id": product_id},
            correlation_id=correlation_id
        )


# Global instance
inter_service_manager = InterServiceManager()


def get_inter_service_manager() -> InterServiceManager:
    """Get inter-service manager instance.
    
    This can be used as a FastAPI dependency.
    """
    return inter_service_manager