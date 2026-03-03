import json
import os
import pandas as pd
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

CHAR_FILE = "data/characters.json"
CHAP_FILE = "data/chapters.json"
CSV_CHAR = "data/Characters.csv"
CSV_CHAP = "data/Chapters.csv"

data_store = {"characters": [], "chapters": []}

def load_data():
    global data_store
    
    def load_resource(json_path, csv_path):
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            try:
                df = pd.read_csv(csv_path, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(csv_path, encoding='latin-1')
            
            data = df.to_dict(orient='records')
            for i, item in enumerate(data):
                item['id'] = i + 1
            return data
    data_store["characters"] = load_resource(CHAR_FILE, CSV_CHAR)
    data_store["chapters"] = load_resource(CHAP_FILE, CSV_CHAP)
    save_data()

def save_data():
    with open(CHAR_FILE, 'w', encoding='utf-8') as f:
        json.dump(data_store["characters"], f, indent=4)
    with open(CHAP_FILE, 'w', encoding='utf-8') as f:
        json.dump(data_store["chapters"], f, indent=4)

class SimpleRESTHandler(BaseHTTPRequestHandler):
    
    def parse_path(self):
        parsed = urlparse(self.path)
        path_parts = parsed.path.strip('/').split('/')
        resource = path_parts[0] if len(path_parts) > 0 else None
        resource_id = path_parts[1] if len(path_parts) > 1 and path_parts[1] else None
        query_params = parse_qs(parsed.query)
        return resource, resource_id, query_params

    def _get_item_index(self, collection_name, item_id):
        try:
            target_id = int(item_id)
            for index, item in enumerate(data_store[collection_name]):
                if int(item.get('id', -1)) == target_id:
                    return index, item
            return None, None
        except ValueError:
            return None, None

    def do_GET(self):
        resource, resource_id, query_params = self.parse_path()

        if resource not in data_store:
            self.send_error(404, "Resource not found")
            return

        current_list = data_store[resource]

        if resource_id:
            _, item = self._get_item_index(resource, resource_id)
            if item:
                self._send_json(item)
            else:
                self.send_error(404, f"Item {resource_id} not found.")
        else:
            filter_data = current_list
            name_filter = query_params.get('name', [None])[0]
            if name_filter:
                filter_data = [i for i in filter_data if name_filter.lower() in str(i.get('name', '')).lower()]
            
            try:
                page = int(query_params.get('page', ['1'])[0])
                limit = int(query_params.get('limit', ['50'])[0])
                start = (page - 1) * limit
                end = start + limit
                self._send_json(filter_data[start:end])
            except ValueError:
                self.send_error(400, "Invalid parameters")

    def do_POST(self):
        resource, resource_id, _ = self.parse_path()
        if resource not in data_store:
            self.send_error(404)
            return
        
        if resource_id:
            self.send_error(405, "Method Not Allowed on individual resource")
            return

        length = int(self.headers.get('Content-Length', 0))
        if length == 0:
            self.send_error(400, "Body required")
            return

        try:
            payload = json.loads(self.rfile.read(length))
            collection = data_store[resource]
            new_id = max([int(x.get('id', 0)) for x in collection], default=0) + 1
            payload['id'] = new_id
            
            collection.append(payload)
            save_data()
            
            self._send_json(payload, 201)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")

    def do_PUT(self):
        resource, resource_id, _ = self.parse_path()
        if resource not in data_store:
            self.send_error(404)
            return

        if not resource_id:
            self.send_error(405, "Method Not Allowed on collection (Bulk update not implemented)")
            return

        length = int(self.headers.get('Content-Length', 0))
        try:
            payload = json.loads(self.rfile.read(length))
            idx, item = self._get_item_index(resource, resource_id)
            
            if item:
                item.update(payload)
                item['id'] = int(resource_id)
                save_data()
                self._send_json(item)
            else:
                self.send_error(404, "Item not found")
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")

    def do_DELETE(self):
        resource, resource_id, _ = self.parse_path()
        if resource not in data_store:
            self.send_error(404)
            return

        if not resource_id:
            self.send_error(405, "Method Not Allowed on collection")
            return

        idx, item = self._get_item_index(resource, resource_id)
        if item:
            deleted = data_store[resource].pop(idx)
            save_data()
            self._send_json({"message": "Deleted", "item": deleted})
        else:
            self.send_error(404, "Item not found")

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode('utf-8'))

def run(port=8000):
    server = HTTPServer(('', port), SimpleRESTHandler)
    print(f"Server running on port {port}")
    server.serve_forever()

if __name__ == '__main__':
    load_data()
    run()