#!/bin/bash

# Time in seconds to wait before locking the screen (30 minutes)
IDLE_TIME=1800

# Function to lock the screen
lock_screen() {
    echo "Locking the screen due to inactivity."
    # Replace the following line with your screen lock command
    cinnamon-session-quit --logout --no-prompt
}

# Get the initial mouse position
initial_mouse_position=$(xdotool getmouselocation --shell | grep -E 'X|Y' | awk -F '=' '{print $2}')

while true; do
    # Sleep for the idle time
    sleep $IDLE_TIME

    # Get the current mouse position
    current_mouse_position=$(xdotool getmouselocation --shell | grep -E 'X|Y' | awk -F '=' '{print $2}')

    # Check if the mouse position has changed
    if [ "$initial_mouse_position" == "$current_mouse_position" ]; then
        # Lock the screen
        lock_screen
    else
        # Update the initial mouse position
        initial_mouse_position=$current_mouse_position
    fi
done