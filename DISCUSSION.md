# Rollback Scenarios - Discussion

## 6/20 Friday

### Main concepts

- store operations in alembic-like versioned files

### User-facing Configuration

- **rollback configuration**
    - location of rollback files
    - automatic rollback
        - on failure
        - manual execution
    - retention of rollback files
        - keep last N files

### New ABC interface

- proper naming of `RollbackCallableTracer`
    - as attributes?
    - inject as parameters of `run` method?
- restrict on serializing `rollback_callable`? or any static method is allowed?

### Serialization

- **custom serialization**
    - pros:
        - the versioned files can be human-readable
    - cons:
        - might have error when serializing new types
        - only handle the following types:
            - basic types
            - Krkn-lib, Krkn-kube, etc. common util class types
- **cloudpickle**
    - https://github.com/cloudpipe/cloudpickle
    - pros:
        - can serialize any Python object
        - handles complex types (e.g., functions, classes)
    - cons:
        - not human-readable


----

Suggestion
- graceful shutdown
- add command option
    - dry run option
- folder_prefix -> replace with run uuid