import os
import logging
import io
import zipfile
import subprocess
import time
from pwnagotchi import plugins
from flask import send_file, render_template_string, redirect

class WebHandshakes(plugins.Plugin):
    __author__ = 'HackerOne'
    __version__ = '5.3'
    __license__ = 'GPL3'
    __description__ = 'HackerOne Full Suite: Todas as funções + Correção de Rede Total.'

    def on_loaded(self):
        self.api_key = 'b3a94578932da256b4a86561806e9ad4'
        logging.info(f"[{self.__author__}] Plugin v{self.__version__} carregado com todas as funções!")

    def check_handshake_offline(self, file_path):
        try:
            if os.path.getsize(file_path) < 100: return "❌ VAZIO"
            with open(file_path, 'rb') as f:
                content = f.read()
                return "✅ VÁLIDO" if b'\x88\x8e' in content else "⚠️ INCOMPLETO"
        except: return "❓ ERRO"

    def on_webhook(self, path, request):
        handshake_dir = "/root/handshakes"
        
        # --- FUNÇÃO: REPARAR REDE (MTU 576 + DNS + HORA) ---
        if path == "fix_net":
            os.system('ifconfig usb0 mtu 576 2>/dev/null')
            os.system('ifconfig eth0 mtu 576 2>/dev/null')
            os.system('echo "nameserver 8.8.8.8" > /etc/resolv.conf')
            os.system('sudo date -s "$(curl -s -I http://google.com | grep -i Date: | cut -d" " -f3-7)"')
            return "Sistema optimizado: MTU 576, DNS e Hora actualizados!", 200

        # --- FUNÇÃO: UPLOAD (COM BYPASS DE ERRO 35) ---
        if path == "upload" or path == "upload_all":
            count = 0
            results = []
            target = "http://104.21.36.196/?api&upload"
            
            if path == "upload":
                files_to_up = [request.args.get('name')]
            else:
                files_to_up = [f for f in os.listdir(handshake_dir) if f.endswith(('.pcap', '.pcapng')) and "✅" in self.check_handshake_offline(os.path.join(handshake_dir, f))]
            
            for fname in files_to_up:
                f_path = os.path.join(handshake_dir, fname)
                # Forçamos HTTP 1.1 e Host Header para evitar inspeção profunda de pacotes do Windows
                cmd = (f'curl -L --http1.1 -H "Host: wpa-sec.st" '
                       f'-F "file=@{f_path}" -F "key={self.api_key}" '
                       f'"{target}" --connect-timeout 30 --limit-rate 40k')
                
                process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if process.returncode == 0:
                    count += 1
                    results.append(f"{fname}: OK")
                else:
                    results.append(f"{fname}: Erro {process.returncode}")
                time.sleep(1)
            return f"Enviados: {count} | Detalhes: {', '.join(results)}", 200

        # --- FUNÇÃO: APAGAR INVÁLIDOS ---
        if path == "clean":
            deleted_count = 0
            for f in os.listdir(handshake_dir):
                if f.endswith(('.pcap', '.pcapng')):
                    status = self.check_handshake_offline(os.path.join(handshake_dir, f))
                    if "✅" not in status:
                        os.remove(os.path.join(handshake_dir, f))
                        deleted_count += 1
            return f"Limpeza concluída! Foram apagados {deleted_count} ficheiros inúteis.", 200

        # --- FUNÇÃO: DOWNLOAD ZIP ---
        if path == "zip":
            memory_file = io.BytesIO()
            with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                for f in os.listdir(handshake_dir):
                    if f.endswith(('.pcap', '.pcapng')):
                        zf.write(os.path.join(handshake_dir, f), f)
            memory_file.seek(0)
            return send_file(memory_file, mimetype='application/zip', as_attachment=True, download_name='handshakes_full.zip')

        # --- FUNÇÃO: DOWNLOAD INDIVIDUAL ---
        if path == "file":
            return send_file(os.path.join(handshake_dir, request.args.get('name')), as_attachment=True)

        # --- RENDERIZAÇÃO DA INTERFACE ---
        try:
            raw_files = sorted([f for f in os.listdir(handshake_dir) if f.endswith(('.pcap', '.pcapng'))])
            files_info = [{'name': f, 'status': self.check_handshake_offline(os.path.join(handshake_dir, f))} for f in raw_files]
        except: return "Erro ao aceder aos ficheiros.", 500

        html = """
        <html>
        <head>
            <title>HackerOne Manager v5.3</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { background: #000; color: #0f0; font-family: 'Courier New', monospace; padding: 20px; }
                .card { max-width: 1000px; margin: auto; border: 2px solid #0f0; padding: 20px; border-radius: 10px; box-shadow: 0 0 20px #0f0; }
                .menu { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 30px; border-bottom: 1px solid #0f0; padding-bottom: 20px; }
                .btn { padding: 12px 20px; color: #000; text-decoration: none; font-weight: bold; border-radius: 5px; background: #0f0; border: none; cursor: pointer; }
                .btn-warn { background: #ff9800; }
                .btn-danger { background: #f44336; }
                .btn-info { background: #00bcd4; }
                .btn-small { padding: 5px 10px; font-size: 0.8em; background: #e91e63; }
                table { width: 100%; border-collapse: collapse; }
                th { text-align: left; color: #fff; background: #111; padding: 10px; }
                td { padding: 10px; border-bottom: 1px solid #333; }
                .status-ok { color: #0f0; }
                .status-err { color: #f44336; }
                a.action-link { color: #00bcd4; text-decoration: none; font-weight: bold; }
                a.action-link:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1 style="text-align:center;">HACKERONE SUITE v5.3</h1>
                <div class="menu">
                    <a href="/plugins/web_handshakes/upload_all" class="btn">🚀 UPLOAD WPA-SEC</a>
                    <a href="/plugins/web_handshakes/zip" class="btn btn-info">📥 BAIXAR TUDO (.ZIP)</a>
                    <a href="/plugins/web_handshakes/fix_net" class="btn btn-warn">🔧 REPARAR REDE/MTU</a>
                    <a href="/plugins/web_handshakes/clean" class="btn btn-danger">🗑️ APAGAR INVÁLIDOS</a>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Nome do Ficheiro</th>
                            <th>Estado EAPOL</th>
                            <th>Ações Disponíveis</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for f in files %}
                        <tr>
                            <td>{{ f.name }}</td>
                            <td class="{{ 'status-ok' if '✅' in f.status else 'status-err' }}">{{ f.status }}</td>
                            <td>
                                <a href="/plugins/web_handshakes/file?name={{ f.name }}" class="action-link">DOWNLOAD</a>
                                {% if '✅' in f.status %}
                                | <a href="/plugins/web_handshakes/upload?name={{ f.name }}" class="btn btn-small">UPLOAD</a>
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        """
        return render_template_string(html, files=files_info)