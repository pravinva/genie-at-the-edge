# Flipbook Quiz Updates - localStorage Persistence

## What Was Fixed

### Issue
- Images weren't loading locally (no `pics/` folder)
- This made the quiz appear broken

### Solution
1. **Images now load from GitHub Pages** - Uses full URLs to your hosted images
2. **Added localStorage persistence** - Scores are saved automatically
3. **Version checking** - Old data is automatically cleared to prevent conflicts
4. **Debug logging** - Console shows what's happening for troubleshooting

## New Features

### 1. Score Persistence
- Scores automatically saved when you mark answers
- Progress restored when you return to the page
- Stores:
  - Correct/incorrect counts
  - Which questions you've answered
  - Your answers (correct/wrong)
  - Timestamp

### 2. Reset Button
- Red button in top-right corner
- Clears all saved progress
- Confirms before deleting

### 3. Version Management
- Storage format version: 2
- Old incompatible data automatically cleared
- Prevents bugs from format changes

### 4. Debug Console
- Open browser console (F12) to see:
  - What questions are answered
  - When progress is saved/loaded
  - Page navigation events

## How It Works

```
1. User opens page
   ↓
2. Load saved progress from localStorage
   ↓
3. User starts quiz, sees blurred images
   ↓
4. User clicks "Reveal Answer"
   ↓
5. Answer shown, user marks correct/wrong
   ↓
6. Progress saved to localStorage
   ↓
7. User can leave and return anytime
   ↓
8. Progress automatically restored
```

## Testing

1. **Open flipbook.html** in browser
2. **Start quiz** and answer a few questions
3. **Close browser completely**
4. **Reopen flipbook.html**
5. **Verify** your scores are restored

## Deployment to GitHub Pages

To update the live version at `https://pravinva.github.io/genie-edge-demo/`:

```bash
# Clone your GitHub Pages repo (if needed)
git clone https://github.com/pravinva/genie-edge-demo.git
cd genie-edge-demo

# Copy the updated file
cp ~/Documents/Demo/genie-at-the-edge/flipbook.html .

# Commit and push
git add flipbook.html
git commit -m "Add localStorage persistence for score tracking

- Auto-save scores when marking answers
- Auto-restore progress on page load
- Add reset button to clear progress
- Add version checking for data compatibility
- Fix image loading to use remote URLs
- Add debug logging for troubleshooting"

git push origin main
```

## File Structure

The updated `flipbook.html` is a single self-contained file that:
- Loads images from: `https://pravinva.github.io/genie-edge-demo/pics/`
- Saves data to: Browser localStorage key `flipbook_quiz_progress`
- Works offline once images are cached

## Customization

To change image location, edit this line in the JavaScript:

```javascript
const IMAGE_BASE_URL = 'https://pravinva.github.io/genie-edge-demo/';
```

Change to:
- `''` - for relative paths (if deploying with images)
- `'pics/'` - for local pics folder
- Any other CDN or hosting URL

## Browser Compatibility

Works in all modern browsers that support:
- localStorage API
- ES6 JavaScript
- CSS animations
- Flexbox

Tested in:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Troubleshooting

If questions aren't showing properly:

1. **Open Browser Console** (F12) and check for errors
2. **Clear localStorage**:
   - Open console and run: `localStorage.removeItem('flipbook_quiz_progress')`
   - Or use the test_clear.html utility
3. **Try Incognito/Private mode** - Tests without cached data
4. **Check Network tab** - Verify images are loading
5. **Verify JavaScript is enabled** in browser settings

## Files Created

- `flipbook.html` - Main quiz file with localStorage persistence
- `test_clear.html` - Utility to clear saved progress
- `FLIPBOOK_UPDATES.md` - This documentation file
