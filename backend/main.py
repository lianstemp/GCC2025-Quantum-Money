from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import math, datetime, random
from qiskit import QuantumCircuit
from qiskit_aer import Aer
from qiskit.compiler import transpile

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
console_logs = []

def log_event(event: str):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    console_logs.append(f"[{timestamp}] {event}")
    if len(console_logs) > 100:
        console_logs.pop(0)

def quantum_random_int(n_bits: int, max_value: int) -> int:
    backend = Aer.get_backend('qasm_simulator')
    random_bits = []
    for _ in range(n_bits):
        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure([0, 1], [0, 1])
        qc_transpiled = transpile(qc, backend)
        job = backend.run(qc_transpiled, shots=1)
        result = job.result().get_counts(qc)
        bitstring = list(result.keys())[0]
        bit = int(bitstring[-1])
        random_bits.append(bit)
    number = 0
    for bit in random_bits:
        number = (number << 1) | bit
    return number if number < max_value else quantum_random_int(n_bits, max_value)

def quantum_random_int_no_entanglement(n_bits: int, max_value: int) -> int:
    backend = Aer.get_backend('qasm_simulator')
    random_bits = []
    for _ in range(n_bits):
        qc = QuantumCircuit(1, 1)
        qc.h(0)
        qc.measure(0, 0)
        qc_transpiled = transpile(qc, backend)
        job = backend.run(qc_transpiled, shots=1)
        result = job.result().get_counts(qc)
        bitstring = list(result.keys())[0]
        bit = int(bitstring)
        random_bits.append(bit)
    number = 0
    for bit in random_bits:
        number = (number << 1) | bit
    return number if number < max_value else quantum_random_int_no_entanglement(n_bits, max_value)

def quantum_random_choice(options: list, use_entanglement: bool = True) -> any:
    n_options = len(options)
    n_bits = math.ceil(math.log2(n_options))
    while True:
        num = quantum_random_int(n_bits, 2**n_bits) if use_entanglement else quantum_random_int_no_entanglement(n_bits, 2**n_bits)
        if num < n_options:
            return options[num]

def classical_random_int(n_bits: int, max_value: int) -> int:
    num = classical_rng.randrange(max_value)
    log_event(f"Classical RNG generated {num}")
    return num

def classical_random_choice(options: list) -> any:
    choice = classical_rng.choice(options)
    log_event(f"Classical RNG choice: {choice}")
    return choice

classical_rng = random.Random(2)
def random_choice(options: list, use_quantum: bool) -> any:
    return quantum_random_choice(options, True) if use_quantum else classical_random_choice(options)

symbols = ["🍒", "🍋", "🍊", "⭐", "🔔", "💎"]
def spin_slot_machine(use_quantum: bool) -> list:
    reels = []
    for _ in range(3):
        reels.append(random_choice(symbols, use_quantum))
    log_event(f"Slot spin (quantum={use_quantum}): {' '.join(reels)}")
    return reels

def slot_attack(use_quantum: bool) -> dict:
    if use_quantum:
        outcome = spin_slot_machine(True)
        log_event("Attack attempted in quantum mode; attack failed")
        return {"status": "fail", "message": "Attack ineffective in quantum mode.", "result": outcome}
    else:
        log_event("Attack successful in classical mode")
        return {"status": "success", "message": "Attack successful! Predicted jackpot outcome.", "result": ["💎", "💎", "💎"]}

current_card_deal = None
def deal_cards(use_quantum: bool, simulate_eavesdrop: bool) -> dict:
    global current_card_deal
    if use_quantum:
        card1 = random_choice(list(range(1, 11)), True)
        card2 = random_choice(list(range(1, 11)), True)
        total = card1 + card2
        current_card_deal = {"card1": card1, "card2": card2, "sum": total, "use_quantum": use_quantum}
        return {"card1": "?" if simulate_eavesdrop else card1, "card2": "?" if simulate_eavesdrop else card2, "sum": total if not simulate_eavesdrop else None, "message": "Error! Tampering detected: Qubits disturbed." if simulate_eavesdrop else "Cards dealt in quantum mode."}
    else:
        card1 = classical_rng.randint(1, 10)
        card2 = classical_rng.randint(1, 10)
        total = card1 + card2
        current_card_deal = {"card1": card1, "card2": card2, "sum": total, "use_quantum": use_quantum}
        log_event(f"Dealt cards (classical): {card1} + {card2} = {total}")
        return {"card1": card1, "card2": card2, "sum": total, "message": "Classical eavesdropping: Cards and sum revealed!" if simulate_eavesdrop else "Cards dealt in classical mode. Target revealed."}

def guess_cards(player1: int, player2: int) -> dict:
    if current_card_deal is None:
        return {"error": "No cards have been dealt yet."}
    total = current_card_deal["sum"]
    diff1 = abs(player1 - total)
    diff2 = abs(player2 - total)
    winner = "Player 1" if diff1 < diff2 else "Player 2" if diff2 < diff1 else "Tie"
    log_event(f"Card game guess: target {total}, P1: {player1}, P2: {player2}, winner: {winner}")
    return {"target": total, "player1_guess": player1, "player2_guess": player2, "winner": winner}

@app.get("/", response_class=HTMLResponse)
async def landing():
    return FileResponse("frontend/src/index.html")

@app.get("/slot", response_class=HTMLResponse)
async def slot_page():
    return FileResponse("frontend/src/slot.html")

@app.get("/card", response_class=HTMLResponse)
async def card_page():
    return FileResponse("frontend/src/card.html")

@app.get("/api/spin", response_class=JSONResponse)
async def api_spin(use_quantum: bool = Query(True), simulate_eavesdrop: bool = Query(False)):
    if simulate_eavesdrop:
        if use_quantum:
            return JSONResponse(status_code=500, content={"error": "Quantum eavesdropping error: Qubits disturbed!"})
        else:
            result = spin_slot_machine(use_quantum)
            return {"result": result, "use_quantum": use_quantum, "message": "Classical eavesdropping: outcome revealed!"}
    else:
        result = spin_slot_machine(use_quantum)
        return {"result": result, "use_quantum": use_quantum}

@app.get("/api/attack", response_class=JSONResponse)
async def api_attack(use_quantum: bool = Query(True), simulate_eavesdrop: bool = Query(False)):
    if simulate_eavesdrop:
        if use_quantum:
            return JSONResponse(status_code=500, content={"error": "Quantum eavesdropping error: Qubits disturbed during attack!"})
        else:
            result = slot_attack(use_quantum)
            result["message"] += " (Classical eavesdropping simulated)"
            return result
    else:
        result = slot_attack(use_quantum)
        return result

@app.get("/api/card/deal", response_class=JSONResponse)
async def api_card_deal(use_quantum: bool = Query(True), simulate_eavesdrop: bool = Query(False)):
    try:
        result = deal_cards(use_quantum, simulate_eavesdrop)
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/card/guess", response_class=JSONResponse)
async def api_card_guess(player1: int, player2: int):
    result = guess_cards(player1, player2)
    return result

@app.get("/api/console", response_class=JSONResponse)
async def api_console():
    return {"logs": console_logs}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)