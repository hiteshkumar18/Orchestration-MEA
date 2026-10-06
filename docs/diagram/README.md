# Data-flow diagram

`layout.py` is the single source of truth — boxes, zones and arrows as data.
Everything else renders from it, so the pictures cannot drift apart.

    python make_svg.py          # orchestrator_dataflow.svg
    python make_docx_image.py   # Word doc with the rendered diagram + notes
    python make_docx_shapes.py  # Word doc with native, editable shapes

Change a box or an arrow in `layout.py` and re-run all three.
`make_docx_image.py` needs the PNG, so run `make_svg.py` and convert it first:

    python -c "import cairosvg; cairosvg.svg2png(url='orchestrator_dataflow.svg', \
        write_to='orchestrator_dataflow.png', output_width=2400, background_color='white')"
