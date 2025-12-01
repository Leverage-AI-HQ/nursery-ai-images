# 🎨 AI Image Generator for Nursery Rhymes

**Part of the Leverage AI Nursery Rhyme Production System**

This tool turns your image ideas into beautiful pictures perfect for any video format - landscape for YouTube or portrait for TikTok and Instagram! Just write what you want to see, and AI creates it for you in the perfect size.

---

## 🤔 What Does This Do?

This script reads a list of image descriptions from a simple text file and automatically creates high-quality pictures in the perfect size for videos. Here's the magic behind it:

**For Landscape (16:9) - Default:**
1. **Step 1:** AI creates your image (1536×1024 pixels)
2. **Step 2:** AI extends it horizontally (1824×1024 pixels) - perfect for YouTube videos!

**For Portrait (9:16) - Social Media:**
1. **Step 1:** AI creates your image (1024×1536 pixels)
2. **Step 2:** AI extends it vertically (1024×1824 pixels) - perfect for TikTok, Instagram Reels, YouTube Shorts!

Think of it like this: the AI makes your picture, then smartly adds more content around the edges to make it fit perfectly in your chosen format.

---

## 📂 Where Do My Images Go?

After running the script, you'll find your images here:

- **`generated_images/`** - Your finished pictures ready to use!
  - Files are named `1.png`, `2.png`, `3.png`, etc. (matching the line numbers in your prompt file)
  - Size will be 1824×1024 for landscape (16:9) or 1024×1824 for portrait (9:16)

- **`generated_images/debug/`** - Behind-the-scenes files (optional to look at)
  - Canvas and mask files used during the generation process

---

## 🚀 Getting Started

### Step 1: Install What You Need

Open your terminal and type:

```bash
pip install -r requirements.txt
```

This installs all the tools the script needs to work.

### Step 2: Add Your API Keys

You need accounts with two AI services: **OpenAI** and **Replicate**.

Once you have your keys, create a file called `.env` in this folder and add:

```
OPENAI_API_KEY=your-openai-key-here
REPLICATE_API_TOKEN=your-replicate-token-here
```

### Step 3: Create Your Prompt File

Make a file called `input.csv` with your image descriptions - **one per line**. For example:

```
A happy puppy playing in a sunny meadow
A castle on top of a mountain at sunset
Children playing in a colorful playground
```

**Tip:** You can leave blank lines - the script will skip them automatically!

---

## 💡 How to Use It

### Generate All Your Images (Landscape - Default)

```bash
python nursery_ai.py
```

This reads `input.csv` and creates all images in 16:9 landscape format.

### Generate Portrait Images for Social Media

```bash
python nursery_ai.py --aspect-ratio 9:16
```

Perfect for TikTok, Instagram Reels, and YouTube Shorts!

### Use a Different File

```bash
python nursery_ai.py my_prompts.csv
```

### Test First (Recommended!)

Before creating hundreds of images, test with just a few:

```bash
python nursery_ai.py --limit 5
```

This creates only the first 5 images - perfect for making sure everything works!

### Combine Options

```bash
# Portrait images with custom CSV and limit
python nursery_ai.py my_prompts.csv --aspect-ratio 9:16 --limit 3

# Landscape with limit
python nursery_ai.py --limit 10
```

### All Options

- `csv_file` - Path to your CSV file (default: `input.csv`)
- `--aspect-ratio` - Choose `16:9` (landscape) or `9:16` (portrait) (default: `16:9`)
- `--limit N` - Generate only the first N images (for testing)

### Need Help?

```bash
python nursery_ai.py --help
```

---

## 💰 Important: This Uses Paid APIs

Every image you create costs money because it uses two different AI services:
- OpenAI (for creating the base image)
- Replicate (for extending it to widescreen)

**Always use `--limit` when testing!** This way you won't accidentally spend money on hundreds of images while you're still figuring things out.

---

## 📝 Quick Tips

- ✅ Empty lines in your CSV file are okay - they'll be skipped
- ✅ If one image fails, the script keeps going with the rest
- ✅ Images are numbered by their line in the file (even if that line was blank)
- ✅ Start small with `--limit` to test your prompts before running everything

---

## 🆘 Need Help?

If something isn't working:
1. Make sure your `.env` file has both API keys
2. Check that you installed the requirements (`pip install -r requirements.txt`)
3. Try running with `--limit 1` to test just one image
4. Make sure your CSV file has actual text descriptions (not empty!)

---

**Made with ❤️ by Leverage AI**
