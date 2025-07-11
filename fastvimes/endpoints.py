"""Auto-generated API endpoints for FastVimes."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from .dependencies import get_filters, get_limit, get_offset, get_sort
from .rql import RQLFilter
from .forms import FormGenerator
from .services import DatabaseService


class EndpointGenerator:
    """Generate API endpoints for database tables."""

    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.filter_parser = RQLFilter()

    def generate_table_endpoints(self, table_name: str) -> APIRouter:
        """Generate CRUD endpoints for a table."""
        router = APIRouter(prefix=f"/{table_name}", tags=[table_name])

        table_config = self.db_service.get_table_config(table_name)

        # Generate model for the table
        TableModel = self.db_service.get_table_dataclass(table_name)

        # READ endpoints
        @router.get("/")
        async def get_table_data(
            filters: dict = Depends(get_filters),
            limit: int | None = Depends(get_limit),
            offset: int | None = Depends(get_offset),
            sort: str | None = Depends(get_sort),
        ):
            """Get all records from table."""
            table = self.db_service.get_table(table_name)

            # Apply RQL-style filters
            if filters.get("filters"):
                table = self.filter_parser.apply_filters(table, filters["filters"])

            # Apply sorting from RQL
            if filters.get("sort"):
                for field, ascending in filters["sort"]:
                    if hasattr(table, field):
                        column = getattr(table, field)
                        table = table.order_by(column.asc() if ascending else column.desc())
            elif sort:
                if hasattr(table, sort):
                    table = table.order_by(getattr(table, sort))

            # Apply pagination from RQL or direct params
            rql_limit = filters.get("limit")
            rql_offset = filters.get("offset")
            
            if rql_limit and rql_offset:
                table = table.limit(rql_limit, offset=rql_offset)
            elif rql_limit:
                table = table.limit(rql_limit)
            elif limit and offset:
                table = table.limit(limit, offset=offset)
            elif limit:
                table = table.limit(limit)
            elif offset:
                table = table.limit(None, offset=offset)

            # Handle count operation
            if filters.get("count"):
                return {"count": table.count().to_pandas()}

            # Apply field selection
            if filters.get("select"):
                select_fields = filters["select"]
                if all(hasattr(table, field) for field in select_fields):
                    table = table.select(*select_fields)

            # Execute query
            result = self.db_service.execute_query(table)

            # Convert to dict
            if hasattr(result, "to_dict"):
                data = result.to_dict(orient="records")
            else:
                data = []

            return {"data": data, "table": table_name}

        # HTML endpoints
        if table_config.html:

            @router.get("/html", response_class=HTMLResponse)
            async def get_table_html(request: Request):
                """Get HTML view of table."""
                table = self.db_service.get_table(table_name)
                result = self.db_service.execute_query(table)

                if hasattr(result, "to_dict"):
                    data = result.to_dict(orient="records")
                else:
                    data = []

                # Generate simple HTML table
                html = f"""
                <h1>{table_name.title()}</h1>
                <table>
                    <thead>
                        <tr>
                """

                if data:
                    for field in data[0].keys():
                        html += f"<th>{field}</th>"

                html += """
                        </tr>
                    </thead>
                    <tbody>
                """

                for record in data:
                    html += "<tr>"
                    for value in record.values():
                        html += f"<td>{value}</td>"
                    html += "</tr>"

                html += """
                    </tbody>
                </table>
                """

                return html

        @router.get("/schema")
        async def get_table_schema():
            """Get table schema."""
            table = self.db_service.get_table(table_name)
            schema = table.schema()

            return {
                "table": table_name,
                "fields": {name: str(type_) for name, type_ in schema.items()},
            }



        # More HTML endpoints
        if table_config.html:

            @router.get("/html/new", response_class=HTMLResponse)
            async def get_new_record_form():
                """Get form for creating new record."""
                form_generator = FormGenerator(self.db_service)
                form_html = form_generator.generate_form(
                    TableModel, action=f"/{table_name}", method="POST"
                )
                return f"<h1>New {table_name.title()}</h1>{form_html}"



        # WRITE endpoints (only if table is writable)
        if table_config.mode == "readwrite":

            @router.post("/")
            async def create_table_record(record: TableModel):
                """Create a new record."""
                table = self.db_service.get_table(table_name)

                # Insert record using Ibis API
                record_dict = record.model_dump()

                # Use Ibis insert API for safe insertion
                insert_expr = table.insert(record_dict)
                self.db_service.execute_query(insert_expr)

                # Return the created record
                return record_dict

            @router.put("/")
            async def update_table_records(
                record: TableModel,
                filters: dict = Depends(get_filters),
            ):
                """Update records using RQL-style filtering."""
                if not filters:
                    raise HTTPException(
                        status_code=400, 
                        detail="PUT requires filters - use query parameters like ?eq(id,123)"
                    )
                
                table = self.db_service.get_table(table_name)
                
                # Apply filters to build WHERE condition
                filtered_table = self.filter_parser.apply_filters(table, filters.get("filters", {}))
                
                # Update record using Ibis API
                record_dict = record.model_dump()
                
                # Use Ibis update API for safe updates
                update_expr = filtered_table.update(record_dict)
                self.db_service.execute_query(update_expr)
                
                # Return updated record
                return record_dict

            @router.delete("/")
            async def delete_table_records(
                filters: dict = Depends(get_filters),
            ):
                """Delete records using RQL-style filtering."""
                if not filters:
                    raise HTTPException(
                        status_code=400, 
                        detail="DELETE requires filters - use query parameters like ?eq(id,123)"
                    )
                
                table = self.db_service.get_table(table_name)
                
                # Apply filters to build WHERE condition
                filtered_table = self.filter_parser.apply_filters(table, filters.get("filters", {}))
                
                # Use Ibis delete API for safe deletion
                delete_expr = filtered_table.delete()
                self.db_service.execute_query(delete_expr)
                
                return {"message": "Records deleted"}

        else:
            # Add read-only endpoints that return 403
            @router.post("/")
            async def create_table_record_readonly(record: TableModel):
                """Create operation not allowed in read-only mode."""
                raise HTTPException(status_code=403, detail="Table is read-only")

            @router.put("/")
            async def update_table_records_readonly(
                record: TableModel,
                filters: dict = Depends(get_filters),
            ):
                """Update operation not allowed in read-only mode."""
                raise HTTPException(status_code=403, detail="Table is read-only")

            @router.delete("/")
            async def delete_table_records_readonly(
                filters: dict = Depends(get_filters),
            ):
                """Delete operation not allowed in read-only mode."""
                raise HTTPException(status_code=403, detail="Table is read-only")

        return router

    def generate_meta_endpoints(self) -> APIRouter:
        """Generate meta endpoints for the API."""
        router = APIRouter(tags=["meta"])

        @router.get("/tables")
        async def list_tables():
            """List all available tables."""
            tables = self.db_service.list_tables()
            return {
                "tables": {
                    name: {
                        "mode": config.mode,
                        "html": config.html,
                        "primary_key": config.primary_key,
                    }
                    for name, config in tables.items()
                }
            }

        @router.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "database": self.db_service.config.db_path}

        return router

    def generate_dynamic_endpoints(self) -> APIRouter:
        """Generate dynamic endpoints that handle any table."""
        router = APIRouter()

        @router.get("/{table_name}")
        async def get_dynamic_table_data(
            table_name: str,
            filters: dict = Depends(get_filters),
            limit: int | None = Depends(get_limit),
            offset: int | None = Depends(get_offset),
            sort: str | None = Depends(get_sort),
        ):
            """Get all records from any table."""
            # Skip reserved paths
            if table_name in ["admin", "docs", "openapi.json", "redoc"]:
                raise HTTPException(status_code=404, detail="Not found")

            # Discover table dynamically
            table = self.db_service.get_table(table_name)

            # Apply RQL-style filters
            if filters.get("filters"):
                table = self.filter_parser.apply_filters(table, filters["filters"])

            # Apply sorting
            if sort:
                if hasattr(table, sort):
                    table = table.order_by(getattr(table, sort))

            # Apply pagination
            if limit and offset:
                table = table.limit(limit, offset=offset)
            elif limit:
                table = table.limit(limit)
            elif offset:
                table = table.limit(None, offset=offset)

            # Execute query
            result = self.db_service.execute_query(table)

            # Convert to dict
            if hasattr(result, "to_dict"):
                data = result.to_dict(orient="records")
            else:
                data = []

            return {"data": data, "table": table_name}

        @router.get("/{table_name}/html", response_class=HTMLResponse)
        async def get_dynamic_table_html(table_name: str, request: Request):
            """Get HTML view of any table."""
            # Skip reserved paths
            if table_name in ["admin", "docs", "openapi.json", "redoc"]:
                raise HTTPException(status_code=404, detail="Not found")

            table = self.db_service.get_table(table_name)
            result = self.db_service.execute_query(table)

            if hasattr(result, "to_dict"):
                data = result.to_dict(orient="records")
            else:
                data = []

            # Generate simple HTML table
            html = f"""
            <h1>{table_name.title()}</h1>
            <table class="table is-fullwidth is-striped">
                <thead>
                    <tr>
            """

            if data:
                for field in data[0].keys():
                    html += f"<th>{field}</th>"

            html += """
                    </tr>
                </thead>
                <tbody>
            """

            for record in data:
                html += "<tr>"
                for value in record.values():
                    html += f"<td>{value}</td>"
                html += "</tr>"

            html += """
                </tbody>
            </table>
            """

            return html

        @router.get("/{table_name}/html/new", response_class=HTMLResponse)
        async def get_dynamic_new_record_form(table_name: str):
            """Get form for creating new record in any table."""
            TableModel = self.db_service.get_table_dataclass(table_name)
            form_generator = FormGenerator(self.db_service)
            form_html = form_generator.generate_form(
                TableModel, action=f"/{table_name}", method="POST"
            )
            return f"<h1>New {table_name.title()}</h1>{form_html}"



        return router
