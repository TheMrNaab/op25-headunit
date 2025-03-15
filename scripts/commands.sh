#!/bin/bash

while true; do
    clear
    echo "========================"
    echo "   Git & OP25 Menu"
    echo "========================"
    echo "1) Pull latest changes (beta branch)"
    echo "2) Check local status"
    echo "3) Show full Git revision (commit hash)"
    echo "4) Show short Git revision"
    echo "5) Show latest tag or commit hash"
    echo "6) Save Git revision to version.txt"
    echo "7) Kill all running rx.py processes"
    echo "8) Read error log"
    echo "9) Clear error log"
    echo "10) Exit"
    echo "========================"
    read -p "Select an option (1-10): " choice

    case $choice in
        1) 
            echo "Pulling latest changes from beta branch..."
            git pull origin beta
            read -p "Press enter to continue..."
            ;;
        2)
            echo "Checking local Git status..."
            git status
            read -p "Press enter to continue..."
            ;;
        3)
            echo "Full Git revision:"
            git rev-parse HEAD
            read -p "Press enter to continue..."
            ;;
        4)
            echo "Short Git revision:"
            git rev-parse --short HEAD
            read -p "Press enter to continue..."
            ;;
        5)
            echo "Latest tag or commit hash:"
            git describe --tags --always
            read -p "Press enter to continue..."
            ;;
        6)
            echo "Saving Git revision to version.txt..."
            git rev-parse --short HEAD > version.txt
            echo "Saved!"
            read -p "Press enter to continue..."
            ;;
        7)
            echo "Killing all rx.py processes..."
            pkill -f rx.py
            echo "Done!"
            read -p "Press enter to continue..."
            ;;
        8)
            echo "Reading error log:"
            cat /opt/op25-project/error.log
            read -p "Press enter to continue..."
            ;;
        9)
            echo "Clearing error log..."
            echo "" > /opt/op25-project/error.log
            echo "Log cleared!"
            read -p "Press enter to continue..."
            ;;
        10)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid choice! Please select a valid option."
            read -p "Press enter to continue..."
            ;;
    esac
done