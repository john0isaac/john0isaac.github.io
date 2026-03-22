# John Aziz Site

Welcome! This repository contains the source code for John Aziz’s personal website and blog, inspired by Mozilla.org and
built with [MkDocs](https://www.mkdocs.org/) and deployed via GitHub Pages.

## 🚀 Getting Started

### Prerequisites

- [Python 3.11+](https://www.python.org/downloads/)
- [pip](https://pip.pypa.io/en/stable/)
- [MkDocs](https://www.mkdocs.org/)

### Installation

1. Clone this repository:

   ```sh
   git clone https://github.com/john0isaac/john0isaac.github.io.git
   cd john0isaac.github.io
   ```

2. Create and activate a virtual environment:

   ```sh
   python -m venv .venv
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ```

3. Install dependencies:

   ```sh
   pip install -r requirements.txt
   ```

### Running Locally

Start the local development server:

```sh
make serve
```

Visit [http://localhost:8000](http://localhost:8000) in your browser to view the site.

## 🛠️ Customization

- **Site settings:** Edit `mkdocs.yml` for title, navigation, and theme options.
- **Content:** Add or edit Markdown files in the `src/` folder.
- **Pages:** Modify or add pages like `src/blog.md`, `src/projects.md`, and `src/talks.md`.
- **Design:** Customize styles using MkDocs themes or custom CSS.

## 📦 Deployment

- Push your changes to the main branch of your GitHub repository.
- The site can be built with `mkdocs build` and deployed via GitHub Pages or other static hosting.

## 📝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to open an issue or submit a pull request.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
