"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Card, CardContent } from "@/components/ui/card"
import { Type, FileText } from "lucide-react"

interface TextInputProps {
  onSubmit: (text: string) => void
}

export function TextInput({ onSubmit }: TextInputProps) {
  const [text, setText] = useState("")
  const wordCount = text
    .trim()
    .split(/\s+/)
    .filter((word) => word.length > 0).length

  const handleSubmit = () => {
    if (text.trim()) {
      onSubmit(text.trim())
    }
  }

  return (
    <div className="space-y-4">
      <Card className="rounded-2xl border-0 bg-muted/30">
        <CardContent className="p-6">
          <div className="text-center space-y-4 mb-6">
            <Type className="h-12 w-12 text-muted-foreground mx-auto" />
            <div>
              <p className="text-lg font-medium text-foreground">Ketik atau Tempel Teks</p>
              <p className="text-sm text-muted-foreground">
                Masukkan materi yang ingin Anda pelajari dalam bentuk teks
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="text-input">Konten Teks</Label>
                <span className="text-sm text-muted-foreground">{wordCount} kata</span>
              </div>
              <Textarea
                id="text-input"
                placeholder="Tempel atau ketik materi pembelajaran Anda di sini..."
                value={text}
                onChange={(e) => setText(e.target.value)}
                className="min-h-[200px] rounded-xl resize-none"
              />
              <p className="text-xs text-muted-foreground">Minimal 50 kata untuk hasil terbaik</p>
            </div>

            <Button onClick={handleSubmit} disabled={wordCount < 10} className="w-full rounded-xl">
              <FileText className="mr-2 h-4 w-4" />
              Buat Flashcard
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
