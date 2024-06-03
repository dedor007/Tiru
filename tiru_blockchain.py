from flask import Flask, render_template, request, redirect, jsonify
import hashlib
import json
from time import time
from datetime import datetime
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
import base64
import os
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.private_key, self.public_key = self.generate_key_pair()
        self.new_block(previous_hash='1', proof=100)  # Create the genesis block

    def generate_key_pair(self):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()
        return private_key, public_key

    def sign_transaction(self, transaction):
        return self.private_key.sign(
            json.dumps(transaction).encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

    def verify_transaction(self, transaction, signature, public_key):
        try:
            public_key.verify(
                signature,
                json.dumps(transaction).encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except:
            return False

    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount, phone_number):
        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'phone_number': phone_number,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        serial_number = self.generate_serial_number(transaction)
        transaction['serial_number'] = serial_number
        signature = self.sign_transaction(transaction)
        self.current_transactions.append({
            'transaction': transaction,
            'signature': signature
        })
        return self.last_block['index'] + 1

    def generate_serial_number(self, transaction):
        return hashlib.sha256(json.dumps(transaction, sort_keys=True).encode()).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def hash(self, block):
        return hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()

    def proof_of_work(self, last_proof):
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    def valid_proof(self, last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

# Instantiate the Blockchain
blockchain = Blockchain()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transactions')
def view_transactions():
    transactions = blockchain.current_transactions
    return render_template('transactions.html', transactions=transactions)

@app.route('/transactions/new', methods=['GET', 'POST'])
def new_transaction():
    if request.method == 'POST':
        values = request.form
        required = ['sender', 'recipient', 'amount', 'phone_number']
        if not all(k in values for k in required):
            return 'Missing values', 400
        index = blockchain.new_transaction(
            values['sender'], 
            values['recipient'], 
            values['amount'],
            values['phone_number']
        )
        response = {'message': f'Transaction will be added to Block {index}'}
        return redirect('/transactions')
    else:
        return render_template('new_transaction.html')

@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    previous_hash = blockchain.hash(last_block)
    blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'proof': proof,
        'previous_hash': previous_hash,
    }
    return jsonify(response), 200

if __name__ == '__main__':
    # Use the PORT environment variable provided by Heroku
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
