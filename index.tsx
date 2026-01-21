import React, { useState, useRef, ChangeEvent } from 'react';
import { createRoot } from 'react-dom/client';
import { GoogleGenAI } from "@google/genai";

const DEFAULT_PROMPT = `Crop the head and create a 2-inch ID photo with:
1. Blue background
2. Professional business attire
3. Frontal face
4. Slight smile`;

const ASPECT_RATIOS = [
  { label: "1:1 (Square / 2x2 inch)", value: "1:1" },
  { label: "3:4 (Standard Portrait)", value: "3:4" },
  { label: "4:3 (Landscape)", value: "4:3" },
];

function App() {
  const [image, setImage] = useState<string | null>(null);
  const [prompt, setPrompt] = useState(DEFAULT_PROMPT);
  const [nameInput, setNameInput] = useState("");
  const [aspectRatio, setAspectRatio] = useState("1:1");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [overlayConfigJson, setOverlayConfigJson] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const processFile = (file: File) => {
    if (!file.type.startsWith('image/')) {
      setError("Please upload a valid image file.");
      return;
    }
    
    const reader = new FileReader();
    reader.onloadend = () => {
      setImage(reader.result as string);
      setResult(null);
      setError(null);
      setOverlayConfigJson(null);
    };
    reader.readAsDataURL(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const parseNameInput = (input: string) => {
    const trimmed = input.trim();
    if (!trimmed) return { name: "", extraPrompt: "" };

    try {
      if (trimmed.startsWith('{')) {
        const json = JSON.parse(trimmed);
        if (json.image_gen?.prompt) {
          const match = json.image_gen.prompt.match(/'([^']+)'/);
          return { 
            name: match ? match[1] : "", 
            extraPrompt: json.image_gen.prompt 
          };
        }
        if (json.details?.text_content) {
          return { 
            name: json.details.text_content, 
            extraPrompt: "" 
          };
        }
      }
    } catch (e) {
      // Ignore JSON parse errors
    }
    return { name: trimmed, extraPrompt: "" };
  };

  // 1. Modular Config Generator
  const generateOverlayConfig = (nameText: string) => {
    return {
      module: "canvas_name_tag_overlay",
      version: "1.2.0",
      status: "active",
      params: {
        text_content: nameText,
        rendering_engine: "html5_canvas_2d",
        layout: {
          width_ratio: 0.4,       // Tag width relative to image width
          height_ratio: 0.14,     // Tag height relative to image width
          bottom_margin: 0.05,    // Margin from bottom
          border_radius_ratio: 0.1
        },
        style: {
          background_color: "#2563eb",
          text_color: "#ffffff",
          border_color: "#ffffff",
          border_width_ratio: 0.005,
          font_family: "Malgun Gothic, Apple SD Gothic Neo, sans-serif"
        }
      }
    };
  };

  // 2. Updated Overlay Function to use the Modular Config
  const overlayNameTag = async (base64Image: string, config: any) => {
    return new Promise<string>((resolve) => {
      const { text_content } = config.params;
      
      if (!text_content) {
        resolve(base64Image);
        return;
      }

      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        if (!ctx) {
          resolve(base64Image);
          return;
        }

        canvas.width = img.width;
        canvas.height = img.height;

        // Draw original image
        ctx.drawImage(img, 0, 0);

        // Destructure config params
        const { layout, style } = config.params;

        // Calculate Metrics
        const tagWidth = canvas.width * layout.width_ratio;
        const tagHeight = tagWidth * (layout.height_ratio / layout.width_ratio); // Maintain internal aspect
        const x = (canvas.width - tagWidth) / 2;
        const y = canvas.height - tagHeight - (canvas.height * layout.bottom_margin);

        // Draw Tag Background
        ctx.fillStyle = style.background_color;
        ctx.strokeStyle = style.border_color;
        ctx.lineWidth = canvas.width * style.border_width_ratio;
        
        // Rounded Rect
        const r = tagHeight * layout.border_radius_ratio;
        ctx.beginPath();
        ctx.moveTo(x + r, y);
        ctx.lineTo(x + tagWidth - r, y);
        ctx.quadraticCurveTo(x + tagWidth, y, x + tagWidth, y + r);
        ctx.lineTo(x + tagWidth, y + tagHeight - r);
        ctx.quadraticCurveTo(x + tagWidth, y + tagHeight, x + tagWidth - r, y + tagHeight);
        ctx.lineTo(x + r, y + tagHeight);
        ctx.quadraticCurveTo(x, y + tagHeight, x, y + tagHeight - r);
        ctx.lineTo(x, y + r);
        ctx.quadraticCurveTo(x, y, x + r, y);
        ctx.closePath();
        
        ctx.fill();
        ctx.stroke();

        // Draw Text
        ctx.fillStyle = style.text_color;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        // Dynamic font size
        const fontSize = tagHeight * 0.5;
        ctx.font = `bold ${fontSize}px "${style.font_family.split(',')[0].replace(/"/g, '')}", sans-serif`;
        
        ctx.fillText(text_content, x + tagWidth / 2, y + tagHeight / 2);

        resolve(canvas.toDataURL('image/png'));
      };
      img.src = base64Image;
    });
  };

  const generatePhoto = async () => {
    if (!image) return;
    
    setLoading(true);
    setError(null);
    setResult(null);
    setOverlayConfigJson(null);

    try {
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      
      const [mimeType, base64Data] = image.split(';base64,');
      const cleanMimeType = mimeType.replace('data:', '');

      const { name, extraPrompt } = parseNameInput(nameInput);

      // Generate the Modular JSON Config immediately
      const configObject = generateOverlayConfig(name);
      
      // Update State to display this JSON in the UI
      setOverlayConfigJson(JSON.stringify(configObject, null, 2));

      let finalPrompt = prompt;
      if (extraPrompt) {
        finalPrompt += `\n\nAdditional Requirements: ${extraPrompt}`;
      }
      finalPrompt += "\n\nIMPORTANT: Generate the professional portrait. Leave the chest area clean or with a blank name tag placeholder. Do not attempt to write specific text on the name tag.";

      const response = await ai.models.generateContent({
        model: 'gemini-2.5-flash-image',
        contents: {
          parts: [
            {
              inlineData: {
                data: base64Data,
                mimeType: cleanMimeType,
              }
            },
            {
              text: finalPrompt
            }
          ]
        },
        config: {
          imageConfig: {
            aspectRatio: aspectRatio as any,
          }
        }
      });

      let foundImage = false;
      if (response.candidates?.[0]?.content?.parts) {
        for (const part of response.candidates[0].content.parts) {
          if (part.inlineData) {
            const resultBase64 = part.inlineData.data;
            const resultMime = part.inlineData.mimeType || 'image/png';
            const aiImage = `data:${resultMime};base64,${resultBase64}`;
            
            // Pass the Config Object to the overlay function
            const finalImage = await overlayNameTag(aiImage, configObject);
            
            setResult(finalImage);
            foundImage = true;
            break;
          }
        }
      }

      if (!foundImage) {
        throw new Error("No image was generated. The model might have returned only text.");
      }

    } catch (err: any) {
      console.error(err);
      setError(err.message || "An error occurred while generating the image.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>Gemini ID Photo Generator</h1>
      <p className="subtitle">Upload a photo to transform it into a professional ID photo</p>
      
      <div className="container">
        {/* Left Section: Inputs */}
        <div className="section">
          <div>
            <label className="label">1. Upload Source Image</label>
            <div 
              className="upload-area"
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
            >
              {image ? (
                <img src={image} alt="Source" />
              ) : (
                <>
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{color: '#94a3b8', marginBottom: '1rem'}}>
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                    <circle cx="8.5" cy="8.5" r="1.5"/>
                    <polyline points="21 15 16 10 5 21"/>
                  </svg>
                  <p>Click or drag image here</p>
                </>
              )}
              <input 
                type="file" 
                ref={fileInputRef} 
                onChange={handleFileChange} 
                accept="image/*" 
                hidden 
              />
            </div>
          </div>

          <div>
            <label className="label">2. Aspect Ratio</label>
            <select 
              value={aspectRatio} 
              onChange={(e) => setAspectRatio(e.target.value)}
            >
              {ASPECT_RATIOS.map(r => (
                <option key={r.value} value={r.value}>{r.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="label">3. Name / JSON Config</label>
            <input 
              type="text"
              value={nameInput}
              onChange={(e) => setNameInput(e.target.value)}
              placeholder="e.g. 배상진 OR { ... json ... }"
            />
            <p style={{fontSize: '0.8rem', color: '#64748b', marginTop: '0.25rem'}}>
              Enter a name directly, or a JSON prompt. The app will generate the specific JSON config below.
            </p>
          </div>

          <div>
            <label className="label">4. Instruction Prompt</label>
            <textarea 
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
          </div>

          <button 
            onClick={generatePhoto} 
            disabled={!image || loading}
          >
            {loading ? 'Generating...' : 'Generate ID Photo'}
          </button>

          {error && (
            <div className="error-msg">
              {error}
            </div>
          )}
        </div>

        {/* Right Section: Output */}
        <div className="section">
          <label className="label">Result</label>
          <div className="result-area">
            {loading ? (
              <div className="loading-spinner"></div>
            ) : result ? (
              <img src={result} alt="Generated ID Photo" />
            ) : (
              <div style={{color: '#94a3b8', textAlign: 'center'}}>
                <p>Generated image will appear here</p>
              </div>
            )}
          </div>
          
          {result && (
            <a 
              href={result} 
              download="gemini-id-photo.png" 
              style={{textDecoration: 'none'}}
            >
              <button style={{width: '100%', background: '#10b981'}}>
                Download Image
              </button>
            </a>
          )}

          {/* New JSON Display Section */}
          {overlayConfigJson && (
            <div className="json-display-container">
              <label className="label">Modular Overlay Configuration (Auto-Generated)</label>
              <pre className="json-code">
                {overlayConfigJson}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const root = createRoot(document.getElementById('root')!);
root.render(<App />);