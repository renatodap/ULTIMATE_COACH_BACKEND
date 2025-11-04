"""
Base Repository - Abstract Database Access Layer

Provides a clean abstraction over Supabase for database operations.

Benefits:
- Easy to mock for testing
- Database changes isolated
- Consistent error handling
- Clear data access patterns
- Retry logic built-in

Architecture:
- One repository per domain (User, Meal, Activity, etc.)
- All repositories inherit from BaseRepository
- Repositories handle database-specific logic
- Services use repositories (not direct Supabase access)

Usage:
    class UserRepository(BaseRepository):
        async def get_by_id(self, user_id: str) -> Optional[Dict]:
            return await self.get_one("profiles", {"id": user_id})
"""

from abc import ABC
from typing import Dict, Any, List, Optional
import structlog
from app.errors import retry_on_database_error, DatabaseError

logger = structlog.get_logger()


class BaseRepository(ABC):
    """
    Abstract base repository for database access.

    Provides common database operations with error handling and retry logic.
    """

    def __init__(self, supabase_client):
        """
        Initialize repository.

        Args:
            supabase_client: Supabase client for database access
        """
        self.supabase = supabase_client
        self.logger = logger

    @retry_on_database_error(max_retries=3)
    async def get_one(
        self,
        table: str,
        filters: Dict[str, Any],
        select: str = "*"
    ) -> Optional[Dict[str, Any]]:
        """
        Get single record from table.

        Args:
            table: Table name
            filters: Filter conditions (e.g., {"id": "123"})
            select: Fields to select

        Returns:
            Record dict or None if not found

        Raises:
            DatabaseError: On database error
        """
        try:
            query = self.supabase.table(table).select(select)

            for key, value in filters.items():
                query = query.eq(key, value)

            result = query.single().execute()

            return result.data if result.data else None

        except Exception as e:
            self.logger.error(
                "get_one_failed",
                table=table,
                filters=filters,
                error=str(e),
                exc_info=True
            )
            raise DatabaseError(
                message=f"Failed to get record from {table}",
                table=table,
                filters=filters
            )

    @retry_on_database_error(max_retries=3)
    async def get_many(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None,
        select: str = "*",
        order_by: Optional[str] = None,
        order_desc: bool = False,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get multiple records from table.

        Args:
            table: Table name
            filters: Filter conditions
            select: Fields to select
            order_by: Field to order by
            order_desc: Order descending
            limit: Limit number of results

        Returns:
            List of records

        Raises:
            DatabaseError: On database error
        """
        try:
            query = self.supabase.table(table).select(select)

            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)

            if order_by:
                query = query.order(order_by, desc=order_desc)

            if limit:
                query = query.limit(limit)

            result = query.execute()

            return result.data if result.data else []

        except Exception as e:
            self.logger.error(
                "get_many_failed",
                table=table,
                filters=filters,
                error=str(e),
                exc_info=True
            )
            raise DatabaseError(
                message=f"Failed to get records from {table}",
                table=table,
                filters=filters
            )

    @retry_on_database_error(max_retries=3)
    async def create(
        self,
        table: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new record.

        Args:
            table: Table name
            data: Record data

        Returns:
            Created record

        Raises:
            DatabaseError: On database error
        """
        try:
            result = self.supabase.table(table).insert(data).execute()

            if not result.data:
                raise DatabaseError(
                    message=f"Failed to create record in {table}",
                    table=table
                )

            self.logger.info(
                "record_created",
                table=table,
                record_id=result.data[0].get("id") if result.data else None
            )

            return result.data[0]

        except Exception as e:
            self.logger.error(
                "create_failed",
                table=table,
                error=str(e),
                exc_info=True
            )
            raise DatabaseError(
                message=f"Failed to create record in {table}",
                table=table
            )

    @retry_on_database_error(max_retries=3)
    async def update(
        self,
        table: str,
        filters: Dict[str, Any],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update record(s).

        Args:
            table: Table name
            filters: Filter conditions
            data: Update data

        Returns:
            Updated record

        Raises:
            DatabaseError: On database error
        """
        try:
            query = self.supabase.table(table).update(data)

            for key, value in filters.items():
                query = query.eq(key, value)

            result = query.execute()

            if not result.data:
                raise DatabaseError(
                    message=f"No records updated in {table}",
                    table=table,
                    filters=filters
                )

            self.logger.info(
                "record_updated",
                table=table,
                filters=filters
            )

            return result.data[0]

        except Exception as e:
            self.logger.error(
                "update_failed",
                table=table,
                filters=filters,
                error=str(e),
                exc_info=True
            )
            raise DatabaseError(
                message=f"Failed to update record in {table}",
                table=table,
                filters=filters
            )

    @retry_on_database_error(max_retries=3)
    async def delete(
        self,
        table: str,
        filters: Dict[str, Any],
        soft: bool = True
    ) -> bool:
        """
        Delete record(s).

        Args:
            table: Table name
            filters: Filter conditions
            soft: Use soft delete (set deleted_at) vs hard delete

        Returns:
            True if successful

        Raises:
            DatabaseError: On database error
        """
        try:
            if soft:
                # Soft delete - set deleted_at timestamp
                from datetime import datetime
                return await self.update(
                    table,
                    filters,
                    {"deleted_at": datetime.utcnow().isoformat()}
                )
            else:
                # Hard delete
                query = self.supabase.table(table).delete()

                for key, value in filters.items():
                    query = query.eq(key, value)

                result = query.execute()

                self.logger.info(
                    "record_deleted",
                    table=table,
                    filters=filters,
                    soft=soft
                )

                return True

        except Exception as e:
            self.logger.error(
                "delete_failed",
                table=table,
                filters=filters,
                error=str(e),
                exc_info=True
            )
            raise DatabaseError(
                message=f"Failed to delete record from {table}",
                table=table,
                filters=filters
            )

    async def execute_rpc(
        self,
        function_name: str,
        params: Dict[str, Any]
    ) -> Any:
        """
        Execute Supabase RPC function.

        Args:
            function_name: RPC function name
            params: Function parameters

        Returns:
            Function result

        Raises:
            DatabaseError: On database error
        """
        try:
            result = self.supabase.rpc(function_name, params).execute()
            return result.data

        except Exception as e:
            self.logger.error(
                "rpc_failed",
                function_name=function_name,
                error=str(e),
                exc_info=True
            )
            raise DatabaseError(
                message=f"RPC function {function_name} failed",
                function_name=function_name
            )
