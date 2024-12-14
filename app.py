from flask import Flask, request, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fingerprints.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Model
class Fingerprint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    screen_resolution = db.Column(db.String(50))
    fonts = db.Column(db.Text)  # Storing as comma-separated string
    user_agent = db.Column(db.String(200))
    device_name = db.Column(db.String(50))

    def __repr__(self):
        return f"<Fingerprint {self.device_name}>"

# Initialize Database
@app.before_request
def create_tables():
    inspector = inspect(db.engine)
    if not inspector.has_table('fingerprint'):
        db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fingerprint', methods=['POST'])
def fingerprint():
    client_data = request.json
    screen_resolution = client_data.get('screen_resolution', 'Unknown')
    fonts = ','.join(client_data.get('fonts', []))  # Convert list to string
    user_agent = request.user_agent.string

    # Check if fingerprint exists
    fingerprint = Fingerprint.query.filter_by(
        screen_resolution=screen_resolution,
        fonts=fonts,
        user_agent=user_agent
    ).first()

    if fingerprint:
        # Return existing device name
        return jsonify({'message': f"Device recognized: {fingerprint.device_name}"})
    else:
        # Save new fingerprint and prompt for device name
        new_fingerprint = Fingerprint(
            screen_resolution=screen_resolution,
            fonts=fonts,
            user_agent=user_agent,
            device_name=None  # Placeholder until user provides name
        )
        db.session.add(new_fingerprint)
        db.session.commit()
        return jsonify({'message': "New device detected. Please provide a name.", 'device_id': new_fingerprint.id})

@app.route('/save-device-name', methods=['POST'])
def save_device_name():
    data = request.json
    device_id = data.get('device_id')
    device_name = data.get('device_name')

    fingerprint = Fingerprint.query.get(device_id)
    if fingerprint:
        fingerprint.device_name = device_name
        db.session.commit()
        # Return the updated fingerprint with device name
        return jsonify({'message': "Device name saved successfully.", 'fingerprint': {
            'device_id': fingerprint.id,
            'device_name': fingerprint.device_name,
            'screen_resolution': fingerprint.screen_resolution,
            'fonts': fingerprint.fonts,
            'user_agent': fingerprint.user_agent
        }})
    else:
        return jsonify({'error': "Device not found."}), 404

@app.route('/list-fingerprints', methods=['GET'])
def list_fingerprints():
    fingerprints = Fingerprint.query.all()
    fingerprint_list = [{
        'device_id': f.id,
        'device_name': f.device_name,
        'screen_resolution': f.screen_resolution,
        'fonts': f.fonts,
        'user_agent': f.user_agent
    } for f in fingerprints]
    return jsonify({'fingerprints': fingerprint_list})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8555)
