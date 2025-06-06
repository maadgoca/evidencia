import socket
import json
import time
import random

HOST = '127.0.0.1'
PORT = 5500

# Configuración de agentes con posiciones iniciales
agents = {
    'agent1': {'position': [0.0, 0.5, 0.0], 'speed': 0.1, 'last_position': [0.0, 0.5, 0.0]},
    'agent2': {'position': [2.0, 0.5, 0.0], 'speed': 0.15, 'last_position': [2.0, 0.5, 0.0]},
    'agent3': {'position': [-2.0, 0.5, 0.0], 'speed': 0.12, 'last_position': [-2.0, 0.5, 0.0]}
}

def generate_movement(current_pos, speed):
    """Genera movimiento aleatorio suave"""
    return [
        current_pos[0] + (random.random() - 0.5) * speed,
        current_pos[1],  # Mantenemos la misma altura (eje Y)
        current_pos[2] + (random.random() - 0.5) * speed
    ]

def has_position_changed(agent_name, new_position, threshold=0.01):
    """Verifica si la posición cambió significativamente"""
    last_pos = agents[agent_name]['last_position']
    
    distance = ((new_position[0] - last_pos[0])**2 + 
                (new_position[1] - last_pos[1])**2 + 
                (new_position[2] - last_pos[2])**2)**0.5
    
    return distance > threshold

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            print("🔗 Conectado a Unity. Enviando coordenadas...")
            print("⏹️  Presiona Ctrl+C para salir")
            print("🚀 Iniciando simulación...\n")
            
            while True:
                # Actualizar posiciones (movimiento aleatorio)
                any_movement = False
                for agent_name, agent_data in agents.items():
                    new_position = generate_movement(
                        agent_data['position'],
                        agent_data['speed']
                    )
                    
                    # Solo actualizar si hay cambio significativo
                    if has_position_changed(agent_name, new_position):
                        agents[agent_name]['last_position'] = agent_data['position'].copy()
                        agents[agent_name]['position'] = new_position
                        any_movement = True
                
                # Solo enviar datos si hubo movimiento
                if any_movement:
                    # Construir mensaje con coordenadas
                    message = {
                        "type": "position_update",
                        "data": [
                            {
                                "name": agent_name,
                                "position": {
                                    "x": agent_data['position'][0],
                                    "y": agent_data['position'][1],
                                    "z": agent_data['position'][2]
                                }
                            }
                            for agent_name, agent_data in agents.items()
                        ]
                    }
                    
                    # Enviar coordenadas a Unity
                    json_message = json.dumps(message)
                    s.sendall(json_message.encode('utf-8'))
                    
                    # Mostrar solo los agentes que se movieron
                    print(f"\n🔄 MOVIMIENTO DETECTADO - {time.strftime('%H:%M:%S')}")
                    for agent_name, agent_data in agents.items():
                        if has_position_changed(agent_name, agent_data['position'], 0.005):
                            pos = agent_data['position']
                            print(f"   📍 {agent_name}: X={pos[0]:.3f}, Y={pos[1]:.3f}, Z={pos[2]:.3f}")
                    
                    # Recibir confirmación de Unity (opcional)
                    try:
                        s.settimeout(0.05)  # Timeout corto para no bloquear
                        data = s.recv(1024)
                        if data:
                            response = json.loads(data.decode('utf-8'))
                            print(f"   ✓ Unity confirmó recepción")
                        s.settimeout(None)  # Quitar timeout
                    except socket.timeout:
                        pass
                    except Exception as e:
                        s.settimeout(None)
                
                time.sleep(0.1)  # 10 actualizaciones por segundo
                
        except ConnectionRefusedError:
            print("\n❌ Error: No se pudo conectar a Unity. Verifica que:")
            print("   1. Unity esté en ejecución")
            print("   2. El script TCPServer esté activo")
            print("   3. El puerto 5500 esté disponible")
        except KeyboardInterrupt:
            print("\n\n⏹️  Deteniendo el cliente...")
        except Exception as e:
            print(f"\n💥 Error inesperado: {e}")
        finally:
            print("🔌 Conexión cerrada")

if __name__ == "__main__":
    main()