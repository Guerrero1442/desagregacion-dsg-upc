class ProjectError(Exception):
    """Excepción base para errores del proyecto."""

    pass


class DatabaseError(ProjectError):
    """Excepción para errores relacionados con la base de datos."""

    pass


class SourceReadError(ProjectError):
    """Excepción para errores al leer un archivo fuente."""

    pass


class ConfigError(ProjectError):
    """Excepción para errores relacionados con la configuración."""

    pass
