import base64
from flask import Flask, render_template, request
import glob
import tempfile
import openai
import os
import subprocess

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


def generate_prompt(tikz):
    return f"""I am an expert at TikZ.
Here is the TikZ code that fits the following description: {tikz}.
\\documentclass[tikz,margin=2mm]{{standalone}}
\\begin{{document}}
\\begin{{tikzpicture}}"""


def post_process(tikz):
    latex = f"""\\documentclass[tikz,margin=2mm]{{standalone}}

\\begin{{document}}
\\begin{{tikzpicture}}
{tikz}
\\end{{tikzpicture}}
\\end{{document}}"""
    return latex.strip()


@app.route("/", methods=["POST"])
def render_tikz():
    # get tikz description from the form
    tikz_description = request.form.get("tikz_description", "")

    # ask OpenAI to generate the tikz code
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=generate_prompt(tikz_description),
        max_tokens=1024,
        n=1,
        suffix="\\end{tikzpicture}",
        stop=["\\end{tikzpicture}"],
        temperature=0.7,
    )
    tikz_code = post_process(response.choices[0].text)

    with tempfile.NamedTemporaryFile(suffix=".tex") as tex_file:
        print(f"Temporary file location: {tex_file.name}")
        tex_file.write(tikz_code.encode())
        tex_file.flush()
        subprocess.call(
            [
                "pdflatex",
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
                "-border",
                "1x1",
                # "-alpha",
                # "remove",
                # "-background",
                # "none",
                f"{tex_file.name[:-4]}.pdf",
                f"{tex_file.name[:-4]}.png",
            ]
        )

    # instead of using the url_for method, we can use the base64 encoding method
    # # so we don't have to copy the file to the static folder
    with open(f"{tex_file.name[:-4]}.png", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

    # remove the temporary files
    for f in glob.glob(f"{tex_file.name[:-4]}.*"):
        subprocess.call(["rm", "-rf", f])
    return render_template(
        "index.html",
        image_data=encoded_string,
        tikz_code=tikz_code,
        tikz_description=tikz_description,
    )

    # also need to handle the case when the button is clicked but no code is entered
    # as well as the case where the code does not compile


if __name__ == "__main__":
    app.run()
