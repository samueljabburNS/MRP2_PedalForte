"""Ponto de entrada do sistema MRP II - Pedal Forte Bicicletas.

Uso:  python main.py
"""

import menu


def main():
    """Inicia o sistema e trata o encerramento pelo teclado (Ctrl+C)."""
    try:
        menu.iniciar()
    except (KeyboardInterrupt, EOFError):
        print("\nSistema encerrado.")


if __name__ == "__main__":
    main()
