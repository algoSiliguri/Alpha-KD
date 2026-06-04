#!/usr/bin/env python3
import os
import sys
import uuid
import signal
import time
import multiprocessing.shared_memory as shm

def cleanup(signum, frame):
    print(\"\n[Orchestrator] Caught SIGINT. Performing clean shutdown...\")
    # Clean slate ritual: unlink shared memory
    try:
        memory_name = os.environ.get(\"ALPHA_KD_SHM_NAME\", \"alpha_kd_telemetry\")
        memory = shm.SharedMemory(name=memory_name)
        memory.close()
        memory.unlink()
        print(f\"[Orchestrator] Unlinked shared memory: {memory_name}\")
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f\"[Orchestrator] Error during shared memory cleanup: {e}\")
    
    sys.exit(0)

def main():
    # Inject Session ID
    session_id = str(uuid.uuid4())
    os.environ[\"ALPHA_KD_SESSION_ID\"] = session_id
    
    # Define shared memory name
    shm_name = f\"alpha_kd_telemetry_{session_id}\"
    os.environ[\"ALPHA_KD_SHM_NAME\"] = shm_name

    print(f\"[Orchestrator] Starting Alpha-KD with Session ID: {session_id}\")
    
    # Clean slate ritual: ensure any dangling memory is unlinked (though UUID should prevent collisions)
    try:
        memory = shm.SharedMemory(name=shm_name, create=True, size=1024*1024) # 1MB for telemetry
        print(f\"[Orchestrator] Created shared memory: {shm_name}\")
    except FileExistsError:
        print(f\"[Orchestrator] Shared memory {shm_name} already exists. Unlinking and recreating...\")
        memory = shm.SharedMemory(name=shm_name)
        memory.unlink()
        memory = shm.SharedMemory(name=shm_name, create=True, size=1024*1024)
        
    # Set up SIGINT trap
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        print(\"[Orchestrator] Running... (Press Ctrl+C to stop)\")
        while True:
            time.sleep(1)
    except Exception as e:
        print(f\"[Orchestrator] Exception: {e}\")
    finally:
        # If we exit the loop, cleanup
        cleanup(None, None)

if __name__ == \"__main__\":
    main()
