from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import math
import datetime

from qiskit import QuantumCircuit
from qiskit_aer import Aer
from qiskit.compiler import transpile

app = FastAPI()

# Update CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global list to hold log messages for our console UI.
console_logs = []

def log_event(event: str):
    """Add a timestamped event to the console log."""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    console_logs.append(f"[{timestamp}] {event}")
    if len(console_logs) > 100:
        console_logs.pop(0)

# --- QRNG functions ---
def quantum_random_int(n_bits: int, max_value: int) -> int:
    """
    Generates a random integer using entangled qubit pairs.
    Uses a 2-qubit circuit (with entanglement) and rejection sampling.
    """
    backend = Aer.get_backend('qasm_simulator')
    random_bits = []
    for _ in range(n_bits):
        qc = QuantumCircuit(2, 2)
        qc.h(0)        # Put qubit 0 in superposition.
        qc.cx(0, 1)    # Entangle qubit 1 with qubit 0.
        qc.measure([0, 1], [0, 1])
        
        qc_transpiled = transpile(qc, backend)
        job = backend.run(qc_transpiled, shots=1)
        result = job.result().get_counts(qc)
        bitstring = list(result.keys())[0]  # e.g. "00" or "11"
        # Since the qubits are entangled both bits are the same.
        bit = int(bitstring[-1])
        random_bits.append(bit)

    number = 0
    for bit in random_bits:
        number = (number << 1) | bit

    log_event(f"Entangled QRNG: bits {random_bits} => number {number}")
    if number < max_value:
        return number
    else:
        return quantum_random_int(n_bits, max_value)

def quantum_random_int_no_entanglement(n_bits: int, max_value: int) -> int:
    """
    Generates a random integer using non-entangled (single qubit) measurements.
    This simulates a scenario where tampering/eavesdropping is possible.
    """
    backend = Aer.get_backend('qasm_simulator')
    random_bits = []
    for _ in range(n_bits):
        qc = QuantumCircuit(1, 1)
        qc.h(0)
        qc.measure(0, 0)
        qc_transpiled = transpile(qc, backend)
        job = backend.run(qc_transpiled, shots=1)
        result = job.result().get_counts(qc)
        bitstring = list(result.keys())[0]  # "0" or "1"
        bit = int(bitstring)
        random_bits.append(bit)

    number = 0
    for bit in random_bits:
        number = (number << 1) | bit

    log_event(f"Non-entangled QRNG: bits {random_bits} => number {number}")
    if number < max_value:
        return number
    else:
        return quantum_random_int_no_entanglement(n_bits, max_value)

def qrng_random_int(n_bits: int, max_value: int, entangled: bool = True) -> int:
    """Selects the proper QRNG function based on the entanglement mode."""
    if entangled:
        return quantum_random_int(n_bits, max_value)
    else:
        return quantum_random_int_no_entanglement(n_bits, max_value)

def quantum_random_choice(options: list, entangled: bool = True) -> any:
    """
    Chooses one element from the options list using quantum randomness.
    Uses the minimal number of bits required (with rejection sampling).
    """
    n_options = len(options)
    n_bits = math.ceil(math.log2(n_options))
    while True:
        num = qrng_random_int(n_bits, 2 ** n_bits, entangled)
        if num < n_options:
            return options[num]

# --- Slot machine logic ---
symbols = ["🍒", "🍋", "🍊", "⭐", "🔔", "💎"]

def spin_slot_machine(entangled: bool = True) -> list:
    """
    Simulates a slot machine spin.
    Returns three symbols selected using the chosen QRNG method.
    """
    reels = []
    for _ in range(3):
        reels.append(quantum_random_choice(symbols, entangled))
    log_event(f"Spin outcome (entangled={entangled}): {' '.join(reels)}")
    return reels

# --- FastAPI Endpoints ---
@app.get("/api/spin", response_class=JSONResponse)
async def api_spin(entangled: bool = Query(True)):
    """
    API endpoint to spin the slot machine.
    The query parameter `entangled` (default True) determines whether to use entangled QRNG.
    """
    result = spin_slot_machine(entangled)
    return {"result": result, "entangled": entangled}

@app.get("/api/attack", response_class=JSONResponse)
async def api_attack(entangled: bool = Query(True)):
    """
    Simulates an attack (i.e. eavesdropping/tampering) attempt.
    The attack is only effective if entanglement is disabled.
    """
    if entangled:
        # When entanglement is enabled, tampering is prevented.
        normal_spin = spin_slot_machine(entangled=True)
        log_event("Attack attempted but entanglement is enabled; tampering prevented.")
        return {
            "status": "fail",
            "message": "Attack ineffective when entanglement is enabled.",
            "result": normal_spin
        }
    else:
        # Attack using non-entangled QRNG.
        attacker_success_chance = 0.1  
        chance = quantum_random_int_no_entanglement(8, 256) / 255
        if chance < attacker_success_chance:
            result = {"status": "success", "message": "Attack successful! Forced jackpot outcome.", "result": ["💎", "💎", "💎"]}
            log_event("Attack successful! Forced jackpot outcome using non-entangled QRNG.")
        else:
            normal_spin = spin_slot_machine(entangled=False)
            result = {"status": "fail", "message": "Attack failed! Tampering attempt detected.", "result": normal_spin}
            log_event("Attack failed! Non-entangled QRNG tampering did not succeed.")
        return result

@app.get("/api/console", response_class=JSONResponse)
async def get_console_logs():
    """Returns the current console log messages."""
    return {"logs": console_logs}