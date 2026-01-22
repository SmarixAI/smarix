Smarix

for single run --> make system down --> docker compose down
to run again-> docker compose up --build -d container_name_here

mac:
source venv/bin/activate
deactivate


windows: 
venv\Scripts\activate



python main.py

python process_data.py --batch

python generate_embedding.py --batch

python build_indices.py