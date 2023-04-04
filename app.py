from flask import Flask, render_template, request, send_file, url_for
import tempfile
import os
import subprocess

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/", methods=["POST"])
def render_tikz():
    tikz_code = request.form.get("tikz_code", "")
    with tempfile.NamedTemporaryFile(suffix=".tex") as tex_file:
        print(f"Temporary file location: {tex_file.name}")
        tex_file.write(tikz_code.encode())
        tex_file.flush()
        subprocess.call(
            [
                "pdflatex",
                # f"-interaction=nonstopmode -output-directory={os.path.dirname(tex_file.name)}",
                # -interaction=nonstopmode causes it to save the file in current directory
                f"-output-directory={os.path.dirname(tex_file.name)}",
                tex_file.name,
            ]
        )
        subprocess.call(
            [
                "convert",
                "-density",
                "300",
                "-quality",
                "90",
                "-flatten",
                "-sharpen",
                "0x1.0",
                # "-resize",
                # "800x800",
                "-trim",
                "-bordercolor",
                "#FFFFFF",
                # "-border",
                # "1x1",
                # "-alpha",
                # "remove",
                # "-background",
                # "none",
                f"{tex_file.name[:-4]}.pdf",
                f"{tex_file.name[:-4]}.png",
            ]
        )
        # a hacky method that copies the file in the tmp folder to the static folder
        subprocess.call(["cp", f"{tex_file.name[:-4]}.png", "static/"])
    # this by itself just renders the entire image in the browser
    # what we want is to render it using the index.html as a template.
    # return send_file(f"{tex_file.name[:-4]}.png", mimetype="image/png")

    url = url_for("static", filename=f"{os.path.basename(tex_file.name)[:-4]}.png")
    return render_template("index.html", url=url, tikz_code=tikz_code)


if __name__ == "__main__":
    app.run()
