import numpy as np
import plotly.graph_objs as go
from flask import Flask, render_template, jsonify
from scipy.spatial.transform import Rotation as R

class OctahedralComplex:
    def __init__(self, initial_positions=None):
        """
        Initialize an octahedral complex with given or default ligand positions.
        """
        if initial_positions is None:
            initial_positions = np.array([
                [1, 0, 0],   # +x
                [-1, 0, 0],  # -x
                [0, 1, 0],   # +y
                [0, -1, 0],  # -y
                [0, 0, 1],   # +z
                [0, 0, -1]   # -z
            ])
        self.initial_positions = np.array(initial_positions)
        self.positions = self.initial_positions.copy()
    
    def generate_planes(self):
        """
        Generate visualization planes for the octahedral complex.
        Returns coordinates for triangular faces.
        """
        # Define the triangular faces of the octahedron
        faces = [
            [0, 2, 4],  # +x, +y, +z
            [0, 2, 5],  # +x, +y, -z
            [0, 3, 4],  # +x, -y, +z
            [0, 3, 5],  # +x, -y, -z
            [1, 2, 4],  # -x, +y, +z
            [1, 2, 5],  # -x, +y, -z
            [1, 3, 4],  # -x, -y, +z
            [1, 3, 5],  # -x, -y, -z
        ]
        
        plane_coords = []
        for face in faces:
            vertices = self.positions[face]
            plane_coords.append({
                'x': vertices[:, 0].tolist(),
                'y': vertices[:, 1].tolist(),
                'z': vertices[:, 2].tolist()
            })
        
        return plane_coords

    def ray_dutt_twist(self, angle, progression=1.0):
        """
        Perform a Ray-Dutt twist transformation with progressive interpolation.
        Fixed implementation to properly rotate around C3 axis.
        """
        theta = np.deg2rad(angle * progression)
        
        # C3 axis is along the (1,1,1) direction
        axis = np.array([1, 1, 1])
        axis = axis / np.linalg.norm(axis)
        
        # Create rotation matrix around the C3 axis
        rotation = R.from_rotvec(theta * axis)
        
        # Apply rotation to all positions
        self.positions = rotation.apply(self.initial_positions)
        
        return self.positions
    
    def bailar_twist(self, angle, progression=1.0):
        """
        Perform a Bailar twist transformation with progressive interpolation.
        """
        theta = np.deg2rad(angle * progression)
        
        # Define the two triangular faces (top and bottom)
        top_indices = [0, 2, 4]  # +x, +y, +z
        bottom_indices = [1, 3, 5]  # -x, -y, -z
        
        # Create rotation matrices
        top_rotation = R.from_rotvec(theta * np.array([0, 0, 1]))
        bottom_rotation = R.from_rotvec(-theta * np.array([0, 0, 1]))
        
        # Copy initial positions
        self.positions = self.initial_positions.copy()
        
        # Apply rotations
        self.positions[top_indices] = top_rotation.apply(self.initial_positions[top_indices])
        self.positions[bottom_indices] = bottom_rotation.apply(self.initial_positions[bottom_indices])
        
        return self.positions

# Flask Application
app = Flask(__name__)

# Global complex instance
complex_obj = OctahedralComplex()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/initial_data')
def initial_data():
    """Provide initial octahedral complex data with planes"""
    return jsonify({
        'positions': complex_obj.positions.tolist(),
        'edges': [
            [0, 1], [2, 3], [4, 5],  # axes
            [0, 2], [0, 4], [1, 3], [1, 5], [2, 4], [2, 5], [3, 4], [3, 5]  # other edges
        ],
        'planes': complex_obj.generate_planes()
    })

@app.route('/animate_twist', methods=['POST'])
def animate_twist():
    from flask import request
    
    twist_type = request.json.get('twist_type', 'ray_dutt')
    max_angle = request.json.get('angle', 45)
    num_frames = request.json.get('frames', 30)
    
    frames = []
    for i in range(num_frames + 1):
        progression = i / num_frames
        
        if twist_type == 'ray_dutt':
            positions = complex_obj.ray_dutt_twist(max_angle, progression)
        else:  # bailar twist
            positions = complex_obj.bailar_twist(max_angle, progression)
        
        frames.append({
            'positions': positions.tolist(),
            'edges': [
                [0, 1], [2, 3], [4, 5],
                [0, 2], [0, 4], [1, 3], [1, 5], [2, 4], [2, 5], [3, 4], [3, 5]
            ],
            'planes': complex_obj.generate_planes()
        })
    
    return jsonify(frames)

def create_html_template():
    """Create the HTML template with improved visualization"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Octahedral Complex Twist Simulation</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px; 
            text-align: center;
        }
        #plot { width: 100%; height: 800px; }
        .controls { 
            margin-top: 20px; 
            display: flex; 
            justify-content: center; 
            gap: 10px;
        }
        button { 
            padding: 10px 15px; 
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #45a049;
        }
        .twist-params {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 20px 0;
            gap: 20px;
        }
        select, input[type="number"] {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .legend {
            margin-top: 20px;
            text-align: left;
            padding: 10px;
            background: #f5f5f5;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <h1>Octahedral Complex Twist Simulation</h1>
    <div class="twist-params">
        <select id="twistType">
            <option value="ray_dutt">Ray-Dutt Twist</option>
            <option value="bailar">Bailar Twist</option>
        </select>
        <label>Angle (°): <input type="number" id="twistAngle" value="60" min="0" max="180"></label>
        <label>Frames: <input type="number" id="frameCount" value="60" min="10" max="100"></label>
    </div>

    <div id="plot"></div>

    <div class="controls">
        <button onclick="loadInitialData()">Reset</button>
        <button onclick="animateTwist()">Animate Twist</button>
    </div>

    <div class="legend">
        <h3>Visualization Guide:</h3>
        <p>• Red spheres: Ligand positions</p>
        <p>• Gray lines: Octahedral edges</p>
        <p>• Colored planes: Triangular faces (semi-transparent)</p>
        <p>• Ray-Dutt twist: Rotation around C3 axis (body diagonal)</p>
        <p>• Bailar twist: Counter-rotation of opposite triangular faces</p>
    </div>

    <script>
        let currentPlot = null;

        function createTraces(data) {
            let traces = [];
            
            // Add vertices (ligands)
            traces.push({
                type: 'scatter3d',
                mode: 'markers',
                x: data.positions.map(p => p[0]),
                y: data.positions.map(p => p[1]),
                z: data.positions.map(p => p[2]),
                marker: {
                    size: 8,
                    color: 'red',
                },
                name: 'Ligands'
            });
            
            // Add edges
            data.edges.forEach((edge, i) => {
                traces.push({
                    type: 'scatter3d',
                    mode: 'lines',
                    x: [data.positions[edge[0]][0], data.positions[edge[1]][0]],
                    y: [data.positions[edge[0]][1], data.positions[edge[1]][1]],
                    z: [data.positions[edge[0]][2], data.positions[edge[1]][2]],
                    line: {
                        color: 'gray',
                        width: 3
                    },
                    showlegend: i === 0,
                    name: 'Edges'
                });
            });
            
            // Add planes with different colors
            const colors = ['rgba(255,0,0,0.2)', 'rgba(0,255,0,0.2)', 
                          'rgba(0,0,255,0.2)', 'rgba(255,255,0,0.2)',
                          'rgba(255,0,255,0.2)', 'rgba(0,255,255,0.2)',
                          'rgba(128,0,0,0.2)', 'rgba(0,128,0,0.2)'];
            
            data.planes.forEach((plane, i) => {
                traces.push({
                    type: 'mesh3d',
                    x: plane.x,
                    y: plane.y,
                    z: plane.z,
                    i: [0],
                    j: [1],
                    k: [2],
                    color: colors[i],
                    opacity: 0.6,
                    showlegend: i === 0,
                    name: 'Faces'
                });
            });
            
            return traces;
        }

        function initializePlot(data) {
            let traces = createTraces(data);
            
            let layout = {
                title: 'Octahedral Complex Visualization',
                scene: {
                    camera: {
                        eye: {x: 1.5, y: 1.5, z: 1.5}
                    },
                    aspectmode: 'cube',
                    xaxis: {range: [-2, 2]},
                    yaxis: {range: [-2, 2]},
                    zaxis: {range: [-2, 2]}
                },
                showlegend: true,
                legend: {
                    x: 0.7,
                    y: 0.9
                }
            };
            
            Plotly.newPlot('plot', traces, layout);
            currentPlot = document.getElementById('plot');
        }

        function loadInitialData() {
            $.get('/initial_data', function(data) {
                initializePlot(data);
            });
        }

        function animateTwist() {
            let twistType = $('#twistType').val();
            let angle = parseInt($('#twistAngle').val());
            let frameCount = parseInt($('#frameCount').val());

            $.ajax({
                url: '/animate_twist',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    twist_type: twistType,
                    angle: angle,
                    frames: frameCount
                }),
                success: function(frames) {
                    let frameTraces = frames.map(frame => ({
                        data: createTraces(frame)
                    }));

                    Plotly.animate('plot', frameTraces, {
                        frame: {duration: 50},
                        transition: {duration: 0},
                        mode: 'immediate'
                    });
                }
            });
        }

        $(document).ready(loadInitialData);
    </script>
</body>
</html>
    """
    
    import os
    os.makedirs('templates', exist_ok=True)
    
    with open('templates/index.html', 'w') as f:
        f.write(html_content)

if __name__ == '__main__':
    create_html_template()
    app.run(debug=True)
