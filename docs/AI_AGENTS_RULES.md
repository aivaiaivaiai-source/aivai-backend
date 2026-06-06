# AI Agents — Project Rules

Architecture and workflow constraints for automated assistants working on this codebase.

---

## PostgreSQL ENUM Types Rule

All PostgreSQL ENUM types must be created manually in Alembic migrations.

- Always use `create_type=False` when defining PostgreSQL ENUM objects in migration files.
- Always call `.create(op.get_bind(), checkfirst=True)` explicitly before creating tables that use the ENUM.
- In `downgrade`, always drop tables that use ENUM first, then drop ENUM types with `.drop(op.get_bind(), checkfirst=True)`.
- Never rely on Alembic autogenerate alone for PostgreSQL ENUM creation.
- Always use explicit enum names, for example:
  - `currency_enum`
  - `listing_status_enum`

Any migration that introduces or changes PostgreSQL ENUM types **must** follow this procedure end-to-end; autogenerate output should be reviewed and adjusted before merge.
