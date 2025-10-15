# 🎨 Recon API - Modern Web Dashboard

A beautiful, modern web interface for the Recon API subdomain scanner with gradient design and smooth animations.

## ✨ Features

- **📋 Scan List**: View all recent reconnaissance scans with status indicators
- **📊 Detailed Results**: Click any scan to view detailed subdomain information
- **🔍 Search & Filter**: Search subdomains and filter by live/dead status
- **📸 Screenshot Gallery**: View captured screenshots of live hosts
- **🎨 Modern Gradient Design**: Beautiful blue-to-purple gradient theme
- **📱 Responsive**: Works on desktop, tablet, and mobile devices
- **⚡ Real-time Updates**: Auto-refreshes scan list every 10 seconds
- **🌈 Smooth Animations**: Fade-in effects and hover transitions

## 🚀 Quick Start

### **Option 1: Access via FastAPI (Recommended)**

The web UI is automatically served by FastAPI:

```
http://localhost:8000/dashboard/
```

### **Option 2: Standalone Server**

You can also serve the web UI independently:

```powershell
# Using Python's built-in HTTP server
cd web
python -m http.server 8080
```

Then open: `http://localhost:8080`

## 📁 File Structure

```
web/
├── index.html      # Main HTML structure
├── styles.css      # Modern gradient CSS styling
├── app.js          # JavaScript for API interaction
└── README.md       # This file
```

## 🎯 Usage

### **1. View All Scans**

The homepage displays all recent scans in a card grid layout:
- **Domain name** and **status** (completed, running, pending, failed)
- **Statistics**: Number of subdomains and screenshots
- **Timestamp**: When the scan was created

### **2. View Scan Details**

Click any scan card to view detailed results:
- **Scan information**: Domain, status, timestamps, statistics
- **Subdomains table**: All discovered subdomains with live status
- **Search**: Filter subdomains by name
- **Filter buttons**: Show all, live only, or dead only
- **Screenshots gallery**: View captured screenshots

### **3. Search & Filter**

- **Search box**: Type to filter subdomains by name
- **Filter buttons**:
  - **All**: Show all subdomains
  - **Live**: Show only live hosts (green)
  - **Dead**: Show only dead hosts (gray)

### **4. View Screenshots**

- Click any screenshot card to open full-size image in new tab
- Screenshots are organized by scan job ID
- Fallback image shown if screenshot fails to load

## 🎨 Design Features

### **Color Scheme**

- **Primary Gradient**: Blue (#667eea) to Purple (#764ba2)
- **Background**: Dark theme (#0f0f23)
- **Cards**: Dark blue (#16213e)
- **Text**: Light gray (#e4e4e7)

### **Status Colors**

- **Completed**: Blue-to-cyan gradient
- **Running**: Pink-to-red gradient (pulsing animation)
- **Pending**: Gray
- **Failed**: Pink-to-yellow gradient

### **Animations**

- **Fade-in**: Cards fade in on page load
- **Hover effects**: Cards lift up on hover
- **Pulse**: Running scans pulse to indicate activity
- **Smooth transitions**: All interactions have smooth 0.3s transitions

## 🔧 Configuration

### **API Base URL**

Edit `app.js` to change the API endpoint:

```javascript
const API_BASE_URL = 'http://localhost:8000/api/v1';
```

### **Auto-refresh Interval**

Change the refresh interval (default: 10 seconds):

```javascript
setInterval(() => {
    loadScans();
}, 10000);  // Change to desired milliseconds
```

## 📊 API Endpoints Used

The web UI interacts with these FastAPI endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/scans` | GET | List all scans |
| `/api/v1/scans/{job_id}` | GET | Get scan details |
| `/jobs/{job_id}/screenshots/*.png` | GET | Serve screenshot images |

## 🌐 Browser Compatibility

Tested and working on:
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Edge 90+
- ✅ Safari 14+

## 🎯 Features Breakdown

### **Scan Cards**

Each scan card shows:
- Domain name (large, bold)
- Status badge (colored, uppercase)
- Subdomain count with icon
- Screenshot count with icon
- Creation timestamp (relative time)

### **Subdomains Table**

Columns:
- **Subdomain**: Full subdomain name
- **Status**: Live/Dead badge with color
- **HTTP Code**: Response status code
- **Response Time**: Time in milliseconds
- **Discovered By**: Tool that found the subdomain

### **Screenshots Gallery**

Features:
- Grid layout (3 columns on desktop, 1 on mobile)
- Thumbnail preview (200px height)
- URL label below each screenshot
- Click to open full-size in new tab
- Fallback image if screenshot fails to load

## 🚀 Performance

- **Lazy loading**: Images load as needed
- **Efficient filtering**: Client-side filtering for instant results
- **Minimal dependencies**: Pure vanilla JavaScript (no frameworks)
- **Small footprint**: ~15KB total (HTML + CSS + JS)

## 🎨 Customization

### **Change Color Scheme**

Edit CSS variables in `styles.css`:

```css
:root {
    --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --color-bg: #0f0f23;
    --color-text: #e4e4e7;
    /* ... more variables */
}
```

### **Add New Features**

The code is well-organized and commented:
- **HTML**: Semantic structure with clear sections
- **CSS**: BEM-like naming convention
- **JavaScript**: Modular functions with clear purposes

## 📝 Notes

- **CORS**: Make sure FastAPI has CORS enabled for cross-origin requests
- **Static Files**: FastAPI must serve the `jobs/` directory for screenshots
- **Auto-refresh**: Pauses when viewing scan details to avoid disruption
- **Error Handling**: Graceful fallbacks for API errors and missing images

## 🐛 Troubleshooting

### **"Error loading scans"**

- Check if API server is running: `http://localhost:8000/docs`
- Verify CORS is enabled in FastAPI
- Check browser console for errors

### **Screenshots not loading**

- Verify screenshots exist in `jobs/{job_id}/screenshots/`
- Check FastAPI static file mounting
- Verify file paths in API response

### **Styling issues**

- Clear browser cache
- Check if `styles.css` is loaded (browser DevTools)
- Verify CSS file path in `index.html`

## 🎉 Enjoy!

The web UI provides a beautiful, modern interface for viewing reconnaissance scan results. The gradient design and smooth animations make it a pleasure to use!

**Happy Scanning! 🚀**

