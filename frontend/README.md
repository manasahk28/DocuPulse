# DocuPulse — Frontend

Frontend for **DocuPulse**, an AI-powered document intelligence system that lets users upload documents (PDF, DOCX, TXT) and ask natural-language questions about their content. Built with React 19, TypeScript, and Tailwind CSS v4.

## Tech Stack

| Technology                                                   | Version | Purpose                     |
| ------------------------------------------------------------ | ------- | --------------------------- |
| [React](https://react.dev/)                                  | 19      | UI library                  |
| [TypeScript](https://www.typescriptlang.org/)                | 5.9     | Type-safe JavaScript        |
| [Vite](https://vite.dev/)                                    | 8       | Build tool & dev server     |
| [Tailwind CSS](https://tailwindcss.com/)                     | 4       | Utility-first CSS framework |
| [Axios](https://axios-http.com/)                             | 1.14    | HTTP client                 |
| [React Markdown](https://github.com/remarkjs/react-markdown) | 10      | Markdown rendering          |
| [Lucide React](https://lucide.dev/)                          | 0.500   | Icon library                |

## Features

- **Document Upload** — Drag-and-drop or browse to upload PDF, DOCX, and TXT files (up to 10 MB)
- **Conversational AI Q&A** — Ask questions and follow-ups with multi-turn memory grounded in your uploaded documents
- **Markdown Rendering** — GitHub-flavored markdown support including tables, code blocks, and blockquotes
- **Mauve Haze Theme** — Curated dark-mode Mauve Haze color palette with custom scrollbar styling
- **Responsive Layout** — Two-column desktop layout with slide-in sidebar on mobile

## Project Structure

```
src/
├── api/
│   └── client.ts            # Axios-based API client (upload & query endpoints)
├── components/
│   ├── Chat.tsx              # Conversation interface with message bubbles
│   ├── MarkdownMessage.tsx   # Styled markdown renderer for assistant responses
│   ├── Sidebar.tsx           # File upload sidebar with drag-and-drop
│   └── WelcomeContent.tsx    # Onboarding screen with feature cards
├── hooks/
│   ├── useChat.ts            # Chat state, message history, and auto-scroll
│   └── useUpload.ts          # File selection, upload state, and status
├── pages/
│   └── Home.tsx              # Main page layout and state orchestration
├── App.tsx                   # Root component
├── main.tsx                  # Entry point
└── index.css                 # Global styles & Tailwind import
```

## Architecture

```
App
└── Home
    ├── Sidebar
    │   └── useUpload hook → api/uploadDocument
    └── Chat
        ├── WelcomeContent (shown before upload)
        ├── MarkdownMessage (assistant responses)
        └── useChat hook → api/queryDocument (with conversation history)
```

**Data flow:** User uploads a file → `useUpload` calls the backend → on success, chat is enabled → user asks a question → `useChat` sends the question + chat history to the backend → markdown response is rendered.

## Getting Started

### Prerequisites

- Node.js 18+ & npm
- Backend API running (defaults to `http://localhost:8000`, configurable via `VITE_API_URL`)

### Install Dependencies

```bash
npm install
```

### Run Dev Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173`.

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

### Lint

```bash
npm run lint
```

## Environment Variables

| Variable       | Default                 | Description          |
| -------------- | ----------------------- | -------------------- |
| `VITE_API_URL` | `http://localhost:8000` | Backend API base URL |

## API Integration

The frontend communicates with the backend through two endpoints:

| Function         | Method | Endpoint  | Description                                                           |
| ---------------- | ------ | --------- | --------------------------------------------------------------------- |
| `uploadDocument` | POST   | `/upload` | Multipart file upload (returns `document_id`, `chunk_count`)          |
| `queryDocument`  | POST   | `/query`  | Send a question, receive an AI-generated answer with optional context |

API timeout is set to **120 seconds** to accommodate large document processing.
