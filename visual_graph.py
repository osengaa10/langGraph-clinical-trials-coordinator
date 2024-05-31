from graph import app

# Get the graph as a PNG binary
png_data = app.get_graph().draw_png()

# Save the PNG binary to a file
with open("output.png", "wb") as f:
    f.write(png_data)

# Optionally, open the image using an external viewer (Linux example using `xdg-open`)
import os
os.system("xdg-open output.png")