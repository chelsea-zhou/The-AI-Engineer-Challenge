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

Create a `.env.local` file in the frontend directory with your API keys:

```env
# Backend URL
BACKEND_URL=http://localhost:8000

# Default API Keys (optional)
# Get your OpenAI API key from: https://platform.openai.com/api-keys
NEXT_PUBLIC_OPENAI_API_KEY=sk-your-openai-api-key-here

# Get your Tavily API key from: https://tavily.com
NEXT_PUBLIC_TAVILY_API_KEY=tvly-your-tavily-api-key-here
```

### API Keys

You can configure API keys in two ways:

1. **Environment Variables (Recommended)**: Add your keys to `.env.local` as shown above
2. **Manual Entry**: Enter keys directly in the UI input fields

If you set environment variables, the keys will be pre-filled in the UI. You can still override them by typing new values in the input fields.

**Note**: Environment variables with `NEXT_PUBLIC_` prefix are exposed to the browser, so only use this for development or when you trust your deployment environment.

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