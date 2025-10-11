# Technical Architecture

## Table of Contents

- [System Overview](#system-overview)
- [Component Architecture](#component-architecture)
  - [User Interface Layer (Electron)](#user-interface-layer-electron)
  - [Window Management Layer (Python)](#window-management-layer-python)
- [Data Flow Architecture](#data-flow-architecture)
  - [Configuration Flow](#configuration-flow)
  - [Window Management Flow](#window-management-flow)
- [Communication Protocol](#communication-protocol)
  - [JSON-RPC Message Structure](#json-rpc-message-structure)
  - [Message Format Specification](#message-format-specification)
- [Window Management Architecture](#window-management-architecture)
  - [Detection Engine](#detection-engine)
  - [Arrangement Engine](#arrangement-engine)
- [Multi-Display Support](#multi-display-support)
- [Security Architecture](#security-architecture)
  - [Process Isolation](#process-isolation)
  - [Validation Pipeline](#validation-pipeline)
- [Performance Optimization](#performance-optimization)
  - [Caching Strategy](#caching-strategy)
  - [Parallel Processing](#parallel-processing)
- [Error Handling Architecture](#error-handling-architecture)

## System Overview

The Multi-AI Chat Manager employs a hybrid desktop architecture combining Python for system-level operations and Electron for modern UI presentation.

```mermaid
graph TB
    subgraph "Desktop Application"
        subgraph "User Interface (Electron)"
            UI[User Interface]
            Main[Main Process]
            Renderer[Renderer Process]
        end

        subgraph "Window Management (Python)"
            Core[Core Engine]
            WinMgr[Window Manager]
            Config[Configuration Manager]
        end

        subgraph "External Systems"
            Browser[Web Browsers]
            OS[Operating System]
            AI[AI Service Websites]
        end
    end

    UI <--> Main
    Main <--> Renderer
    Main <--> Core
    Core <--> WinMgr
    Core <--> Config
    WinMgr <--> OS
    WinMgr <--> Browser
    Browser <--> AI
```

The application consists of two main components: User Interface (Electron) for desktop interaction, and Window Management (Python) for core operations. The Python component communicates with the operating system to manage windows and connects to AI services through web browsers.

## Component Architecture

### User Interface Layer (Electron)

```mermaid
graph LR
    subgraph "Electron Application"
        MainProc[Main Process]
        RendProc[Renderer Process]
        Preload[Preload Scripts]

        MainProc --> RendProc
        MainProc --> Preload
        RendProc --> Preload
    end

    subgraph "UI Components"
        Toolbar[Control Toolbar]
        Grid[Application Grid]
        Settings[Settings Panel]
        Status[Status Bar]
    end

    subgraph "State Management"
        AppState[Application State]
        ConfigState[Configuration State]
        WindowState[Window State]
    end

    RendProc --> Toolbar
    RendProc --> Grid
    RendProc --> Settings
    RendProc --> Status

    Toolbar --> AppState
    Grid --> WindowState
    Settings --> ConfigState
```

The User Interface (Electron) consists of a main process handling security and system access, while the renderer process displays the interface. Components include a toolbar for controls, a grid displaying AI applications, settings panels for configuration, and a status bar showing current activity.

### Window Management Layer (Python)

```mermaid
graph TB
    subgraph "Python Core"
        Bridge[Electron Bridge]
        Engine[Core Engine]

        subgraph "Managers"
            WinMgr[Window Manager]
            CfgMgr[Config Manager]
            ProcMgr[Process Manager]
        end

        subgraph "Utilities"
            Logger[Logging System]
            Validator[Config Validator]
            PathUtil[Path Utilities]
        end
    end

    Bridge <--> Engine
    Engine --> WinMgr
    Engine --> CfgMgr
    Engine --> ProcMgr

    WinMgr --> Logger
    CfgMgr --> Validator
    ProcMgr --> PathUtil
```

Window Management (Python) is organized into specialized managers: the Window Manager handles browser windows, Config Manager processes settings, and Process Manager launches applications. Support utilities provide logging, validation, and file path operations.

## Data Flow Architecture

### Configuration Flow

```mermaid
sequenceDiagram
    participant User
    participant UI
    participant Bridge
    participant ConfigMgr
    participant Validator
    participant FileSystem

    User->>UI: Modify Settings
    UI->>Bridge: Update Config Request
    Bridge->>ConfigMgr: Process Changes
    ConfigMgr->>Validator: Validate Schema
    Validator->>ConfigMgr: Validation Result
    ConfigMgr->>FileSystem: Write Config
    FileSystem->>ConfigMgr: Confirm Write
    ConfigMgr->>Bridge: Update Complete
    Bridge->>UI: Refresh Interface
    UI->>User: Show Updated State
```

Configuration changes flow through validation to ensure correctness, get persisted to files, then trigger interface updates to reflect the new settings.

### Window Management Flow

```mermaid
sequenceDiagram
    participant User
    participant UI
    participant Bridge
    participant WinMgr
    participant OS
    participant Browser

    User->>UI: Click "Arrange Windows"
    UI->>Bridge: Arrange Command
    Bridge->>WinMgr: Execute Arrangement
    WinMgr->>OS: Enumerate Windows
    OS->>WinMgr: Window List
    WinMgr->>WinMgr: Filter AI Windows
    WinMgr->>OS: Position Windows
    OS->>Browser: Update Window Positions
    Browser->>OS: Confirm Positions
    OS->>WinMgr: Operation Complete
    WinMgr->>Bridge: Result Data
    Bridge->>UI: Update Status
    UI->>User: Show Completion
```

Window arrangement executes by requesting a list of all open windows from the operating system, filtering for AI application windows, then instructing the OS to position each browser window.

## Communication Protocol

### JSON-RPC Message Structure

```mermaid
graph LR
    subgraph "Electron Process"
        UI[User Interface]
        IPC[IPC Channel]
    end

    subgraph "Python Process"
        Stdin[Standard Input]
        Bridge[JSON-RPC Bridge]
        Handler[Command Handler]
        Stdout[Standard Output]
    end

    UI --> IPC
    IPC --> Stdin
    Stdin --> Bridge
    Bridge --> Handler
    Handler --> Bridge
    Bridge --> Stdout
    Stdout --> IPC
    IPC --> UI
```

The User Interface (Electron) communicates with Window Management (Python) through standard input/output channels using JSON-RPC format for inter-process communication.

### Message Format Specification

**Request Structure:**
```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "method": "window_operation",
  "params": {
    "action": "arrange",
    "layout": "grid",
    "dimensions": {"cols": 4, "rows": 2}
  }
}
```

**Response Structure:**
```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "result": {
    "success": true,
    "windows_arranged": 6,
    "failed_operations": 0
  }
}
```

## Window Management Architecture

### Detection Engine

```mermaid
graph TB
    subgraph "Window Detection Pipeline"
        Enum[Window Enumeration]
        Filter[Title Filtering]
        Validate[Process Validation]
        Cache[Result Caching]

        Enum --> Filter
        Filter --> Validate
        Validate --> Cache
    end

    subgraph "Matching Criteria"
        Keywords[Keyword Patterns]
        Domains[Domain Matching]
        Process[Process Names]

        Keywords --> Filter
        Domains --> Filter
        Process --> Validate
    end

    subgraph "Output"
        AIWindows[AI Window List]
        Metadata[Window Metadata]

        Cache --> AIWindows
        Cache --> Metadata
    end
```

The detection engine finds AI windows by examining all open windows, matching their titles against configured patterns (like "ChatGPT" or "Claude"), verifying browser process ownership, then caching results to avoid immediate re-scanning.

### Arrangement Engine

```mermaid
graph LR
    subgraph "Layout Calculation"
        Display[Display Detection]
        Grid[Grid Calculation]
        Position[Position Mapping]

        Display --> Grid
        Grid --> Position
    end

    subgraph "Window Operations"
        Move[Move Window]
        Resize[Resize Window]
        Focus[Focus Management]

        Position --> Move
        Position --> Resize
        Position --> Focus
    end

    subgraph "Validation"
        Bounds[Boundary Check]
        Overlap[Overlap Prevention]
        State[State Verification]

        Move --> Bounds
        Resize --> Overlap
        Focus --> State
    end
```

The arrangement engine determines screen layout and calculates grid positions, then moves and resizes each window to fit while ensuring windows remain on-screen and non-overlapping.

## Multi-Display Support

```mermaid
graph TB
    subgraph "Display System"
        Primary[Primary Monitor]
        Secondary[Secondary Monitor]
        Virtual[Virtual Desktop]

        Primary -.-> Virtual
        Secondary -.-> Virtual
    end

    subgraph "Arrangement Modes"
        Span[Span Mode]
        Clone[Clone Mode]
        Primary_Only[Primary Only]

        Virtual --> Span
        Primary --> Clone
        Primary --> Primary_Only
    end

    subgraph "Window Distribution"
        GridLayout[Grid Layout]
        SideBySide[Side by Side]
        Custom[Custom Positions]

        Span --> GridLayout
        Clone --> SideBySide
        Primary_Only --> Custom
    end
```

Multi-monitor configurations support spanning windows across all screens for maximum space, duplicating layouts on each screen, or restricting to the primary monitor. The application automatically detects display configurations and presents appropriate options.

## Security Architecture

### Process Isolation

```mermaid
graph TB
    subgraph "Security Boundaries"
        subgraph "Electron Sandbox"
            Renderer[Renderer Process]
            Preload[Preload Context]

            Renderer -.-> Preload
        end

        subgraph "Node.js Context"
            Main[Main Process]
            FileAccess[File System Access]

            Main --> FileAccess
        end

        subgraph "Python Subprocess"
            WinMgmt[Window Management]
            SystemAPI[System API Access]

            WinMgmt --> SystemAPI
        end
    end

    Main <--> WinMgmt
    Main <--> Preload
```

The application maintains security through process isolation: the renderer interface runs in a sandbox with limited permissions, the main process handles files safely, and Window Management (Python) runs in its own process with controlled system access.

### Validation Pipeline

```mermaid
graph LR
    subgraph "Input Validation"
        UserInput[User Input]
        Sanitize[Input Sanitization]
        TypeCheck[Type Validation]

        UserInput --> Sanitize
        Sanitize --> TypeCheck
    end

    subgraph "Configuration Validation"
        Schema[Schema Validation]
        PathCheck[Path Validation]
        Security[Security Scan]

        TypeCheck --> Schema
        Schema --> PathCheck
        PathCheck --> Security
    end

    subgraph "Execution Safety"
        Sandbox[Sandbox Check]
        Privileges[Privilege Validation]
        Execute[Safe Execution]

        Security --> Sandbox
        Sandbox --> Privileges
        Privileges --> Execute
    end
```

## Performance Optimization

### Caching Strategy

```mermaid
graph TB
    subgraph "Cache Layers"
        WindowCache[Window Cache]
        ConfigCache[Configuration Cache]
        DisplayCache[Display Cache]

        WindowCache --> MemoryMgmt[Memory Management]
        ConfigCache --> MemoryMgmt
        DisplayCache --> MemoryMgmt
    end

    subgraph "Cache Policies"
        TTL[Time-based Expiry]
        LRU[Least Recently Used]
        Size[Size-based Limits]

        TTL --> MemoryMgmt
        LRU --> MemoryMgmt
        Size --> MemoryMgmt
    end

    subgraph "Invalidation"
        FileWatch[File System Watcher]
        EventDriven[Event-driven Updates]
        Manual[Manual Refresh]

        FileWatch --> WindowCache
        EventDriven --> ConfigCache
        Manual --> DisplayCache
    end
```

### Parallel Processing

```mermaid
graph LR
    subgraph "Concurrency Model"
        MainThread[Main Thread]
        WorkerPool[Worker Thread Pool]
        AsyncOps[Async Operations]

        MainThread --> WorkerPool
        MainThread --> AsyncOps
    end

    subgraph "Task Distribution"
        WindowOps[Window Operations]
        ConfigLoad[Configuration Loading]
        ProcessMgmt[Process Management]

        WorkerPool --> WindowOps
        WorkerPool --> ConfigLoad
        AsyncOps --> ProcessMgmt
    end

    subgraph "Synchronization"
        Locks[Resource Locks]
        Events[Event Coordination]
        Results[Result Aggregation]

        WindowOps --> Locks
        ConfigLoad --> Events
        ProcessMgmt --> Results
    end
```

## Error Handling Architecture

```mermaid
graph TB
    subgraph "Error Detection"
        Validation[Input Validation]
        Runtime[Runtime Monitoring]
        SystemCheck[System Health Check]
    end

    subgraph "Error Classification"
        UserError[User Input Error]
        SystemError[System Error]
        ConfigError[Configuration Error]
        NetworkError[Network Error]
    end

    subgraph "Recovery Strategies"
        Retry[Automatic Retry]
        Fallback[Fallback Options]
        UserPrompt[User Intervention]
        GracefulDeg[Graceful Degradation]
    end

    Validation --> UserError
    Runtime --> SystemError
    SystemCheck --> ConfigError

    UserError --> UserPrompt
    SystemError --> Retry
    ConfigError --> Fallback
    NetworkError --> GracefulDeg
```

This architecture ensures reliable and secure operation while keeping components separated and using resources efficiently.