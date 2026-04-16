# USB Server Client

Tento projekt poskytuje jednoduchý USB-over-IP nástroj s grafickým rozhraním:

- `server.py` - server zobrazující připojená USB zařízení a umožňující je bindovat pro vzdálené klienty
- `client.py` - klient, který načte dostupná USB zařízení ze serveru a připojí je jako lokální zařízení
- `common.py` - společné funkce pro spuštění `usbip` a parsování výstupu

## Požadavky

- Linux / Debian / Ubuntu
- Python 3
- `usbip`, `usbipd`
- `python3-tk` pro Tkinter GUI

## Instalace

Spusťte instalační skript:

```bash
cd "$(pwd)"
./install.sh
```

Pokud skript není spustitelný, nastavte práva:

```bash
chmod +x install.sh
./install.sh
```

## Spuštění

1. Spusťte server:

```bash
python3 server.py
```

2. Spusťte klienta v jiném okně nebo na jiném počítači:

```bash
python3 client.py
```

3. V klientu zadejte IP adresu serveru a klikněte na `Obnovit dostupná zařízení`.
4. Vyberte jedno nebo více zařízení a klikněte na `Připojit vybrané`.

## Poznámky

- Pro `bind`, `unbind` a `attach` může být potřeba práva root / `sudo`.
- Pokud port `5000` již používá jiný proces, upravte zdrojový kód nebo ukončete konflikt.
- `server.py` a `client.py` mají jednoduchou GUI logiku pomocí Tkinter.
