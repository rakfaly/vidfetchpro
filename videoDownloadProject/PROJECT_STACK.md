# Project Stack and Setup

**Frameworks and Core Libraries**
- Django (web framework)
- Celery (background tasks)
- django-celery-results (task result backend)
- django-htmx (HTMX integration)
- django-tailwind (Tailwind CSS integration)
- django-browser-reload (dev auto-reload)
- python-dotenv (env file support)
- psycopg2-binary (PostgreSQL driver)
- yt-dlp (video metadata + downloads)

**System Dependencies (Homebrew)**
- `brew install python`
- `brew install postgresql` (if you use Postgres)
- `brew install ffmpeg` (yt-dlp post-processing)
- `brew install deno` (yt-dlp JS challenge solver)
- `brew install node` (Tailwind build tooling)
- `brew install tree-sitter` (Neovim Treesitter)
- `brew install ripgrep`
- `brew install fd`
- `brew install --cask kitty`
- `brew install neovim`

**Python Install Commands**
- `python -m venv venv`
- `source venv/bin/activate`
- `pip install -r requirements/prod.txt`
- `pip install -r requirements/dev.txt` (dev only)

**Neovim (lazy.nvim) Plugins**
- `folke/lazy.nvim`
- `nvim-lua/plenary.nvim`
- `nvim-tree/nvim-web-devicons`
- `folke/tokyonight.nvim`
- `folke/which-key.nvim`
- `nvim-lualine/lualine.nvim`
- `lewis6991/gitsigns.nvim`
- `numToStr/Comment.nvim`
- `tpope/vim-fugitive`
- `windwp/nvim-autopairs`
- `folke/todo-comments.nvim`
- `folke/trouble.nvim`
- `akinsho/toggleterm.nvim`
- `L3MON4D3/LuaSnip`
- `rafamadriz/friendly-snippets`
- `hrsh7th/nvim-cmp`
- `hrsh7th/cmp-nvim-lsp`
- `hrsh7th/cmp-buffer`
- `hrsh7th/cmp-path`
- `saadparwaiz1/cmp_luasnip`
- `stevearc/conform.nvim`
- `mfussenegger/nvim-lint`
- `lepture/vim-jinja`
- `mattn/emmet-vim`
- `NvChad/nvim-colorizer.lua`
- `williamboman/mason.nvim`
- `williamboman/mason-lspconfig.nvim`
- `WhoIsSethDaniel/mason-tool-installer.nvim`
- `neovim/nvim-lspconfig`
- `nvim-tree/nvim-tree.lua`
- `nvim-telescope/telescope.nvim`
- `nvim-treesitter/nvim-treesitter`
- `windwp/nvim-ts-autotag`

**Mason-Managed Tools (Auto-Installed by Neovim)**
- LSP servers: `lua_ls`, `pyright`, `ruff`, `html`, `cssls`, `tailwindcss`, `emmet_language_server`, `ts_ls`, `jsonls`, `yamlls`, `bashls`
- Formatters: `black`, `isort`, `prettier`, `prettierd`, `stylua`, `shfmt`, `djlint`
- Linters: `ruff`, `djlint`
