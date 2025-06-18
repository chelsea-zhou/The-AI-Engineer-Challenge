# 🚀 AI Chat Interface Frontend

A beautiful, modern chat interface for OpenAI's powerful language models! Built with Next.js, TypeScript, and Tailwind CSS.

## ✨ Features

- **Real-time Streaming**: Watch AI responses appear word by word in real-time
- **Modern UI**: Clean, responsive design with dark mode support
- **Model Selection**: Choose from different OpenAI models (GPT-4.1 Mini, GPT-4, GPT-3.5 Turbo)
- **System Messages**: Customize the AI's behavior with system prompts
- **Secure API Key Input**: Password-style input for your OpenAI API key
- **Message History**: View your conversation history with timestamps
- **Auto-scroll**: Automatically scrolls to new messages
- **Loading States**: Beautiful loading animations and disabled states

## 🛠️ Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first CSS framework
- **Heroicons** - Beautiful SVG icons
- **Vercel Ready** - Optimized for deployment on Vercel

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ installed
- Your OpenAI API key ready
- Backend API running (see backend setup)

### Installation

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

4. **Open your browser:**
   Navigate to [http://localhost:3000](http://localhost:3000)

### Backend Setup

Make sure your backend API is running on `http://localhost:8000` (or set the `BACKEND_URL` environment variable).

To start the backend:
```bash
cd api
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

## 🔧 Configuration

### Environment Variables

Create a `.env.local` file in the frontend directory:

```env
BACKEND_URL=http://localhost:8000
```

### API Key

1. Get your OpenAI API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Enter it in the "OpenAI API Key" field in the UI
3. The key is stored locally and never sent to our servers

## 🎨 Usage

1. **Enter your API key** in the configuration panel
2. **Select a model** (GPT-4.1 Mini is recommended for cost-effectiveness)
3. **Optionally set a system message** to customize AI behavior
4. **Type your message** and press Enter or click Send
5. **Watch the AI respond** in real-time!

## 🚀 Deployment

### Vercel (Recommended)

1. Push your code to GitHub
2. Connect your repository to Vercel
3. Set the `BACKEND_URL` environment variable in Vercel
4. Deploy! 🎉

### Other Platforms

The app can be deployed to any platform that supports Next.js:
- Netlify
- Railway
- DigitalOcean App Platform
- AWS Amplify

## 🎯 Key Features Explained

### Real-time Streaming
The interface uses the Fetch API's streaming capabilities to display AI responses as they're generated, creating a more engaging user experience.

### Responsive Design
Built with Tailwind CSS, the interface looks great on desktop, tablet, and mobile devices.

### Security
- API keys are never stored on our servers
- All communication is done client-side
- Password input fields for sensitive data

### Accessibility
- Proper ARIA labels
- Keyboard navigation support
- High contrast ratios
- Screen reader friendly

## 🐛 Troubleshooting

### Common Issues

1. **"Failed to get response" error**
   - Check that your backend API is running
   - Verify your API key is correct
   - Ensure the `BACKEND_URL` environment variable is set correctly

2. **CORS errors**
   - Make sure your backend has CORS properly configured
   - Check that the frontend is making requests to the correct backend URL

3. **Build errors**
   - Run `npm install` to ensure all dependencies are installed
   - Check that you're using Node.js 18+

### Getting Help

If you encounter any issues:
1. Check the browser console for error messages
2. Verify your backend API is running and accessible
3. Ensure your OpenAI API key is valid and has sufficient credits

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

**Happy chatting! 🤖✨**