from flask import Flask, request, jsonify
import subprocess
import json
import os

app = Flask(__name__)

# Caminho para o arquivo notes.json temporário
NOTES_FILE = "notes.json"

@app.route("/update-release-notes", methods=["POST"])
def update_release_notes():
    try:
        # Recebe os dados da requisição
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid input data"}), 400

        # Baixa o arquivo notes.json do bucket
        download_command = [
            "mgc", "object-storage", "objects", "download",
            "--src=release-notes-docs/notes.json"
        ]
        subprocess.run(download_command, check=True)

        # Carrega o arquivo notes.json existente
        if os.path.exists(NOTES_FILE):
            with open(NOTES_FILE, "r") as f:
                notes = json.load(f)
        else:
            notes = []

        # Adiciona o novo objeto ao início do arquivo
        notes.insert(0, data)

        # Salva o arquivo atualizado
        with open(NOTES_FILE, "w") as f:
            json.dump(notes, f, indent=2)

        # Faz o upload do arquivo atualizado para o bucket
        upload_command = [
            "mgc", "object-storage", "objects", "upload",
            f"--src={NOTES_FILE}", "--dst=release-notes-docs"
        ]
        subprocess.run(upload_command, check=True)

        # Define as permissões do arquivo como public-read
        acl_command = [
            "mgc", "object-storage", "objects", "acl", "set",
            "release-notes-docs/notes.json", "--public-read"
        ]
        subprocess.run(acl_command, check=True)

        return jsonify({"message": "Release notes updated successfully"}), 200

    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Command failed: {e}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
