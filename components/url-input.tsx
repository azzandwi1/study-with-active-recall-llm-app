"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent } from "@/components/ui/card"
import { LinkIcon, Globe } from "lucide-react"

interface URLInputProps {
  onSubmit: (url: string) => void
}

export function URLInput({ onSubmit }: URLInputProps) {
  const [url, setUrl] = useState("")
  const [isValid, setIsValid] = useState(false)

  const validateURL = (input: string) => {
    try {
      new URL(input)
      return true
    } catch {
      return false
    }
  }

  const handleInputChange = (value: string) => {
    setUrl(value)
    setIsValid(validateURL(value))
  }

  const handleSubmit = () => {
    if (isValid && url.trim()) {
      onSubmit(url.trim())
    }
  }

  return (
    <div className="space-y-4">
      <Card className="rounded-2xl border-0 bg-muted/30">
        <CardContent className="p-6">
          <div className="text-center space-y-4 mb-6">
            <Globe className="h-12 w-12 text-muted-foreground mx-auto" />
            <div>
              <p className="text-lg font-medium text-foreground">Masukkan URL Artikel</p>
              <p className="text-sm text-muted-foreground">
                Kami akan mengekstrak konten dari halaman web yang Anda berikan
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="url-input">URL Artikel atau Halaman Web</Label>
              <div className="relative">
                <LinkIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="url-input"
                  type="url"
                  placeholder="https://example.com/artikel-menarik"
                  value={url}
                  onChange={(e) => handleInputChange(e.target.value)}
                  className="pl-10 rounded-xl"
                />
              </div>
              {url && !isValid && <p className="text-sm text-destructive">Format URL tidak valid</p>}
            </div>

            <Button onClick={handleSubmit} disabled={!isValid || !url.trim()} className="w-full rounded-xl">
              Ekstrak Konten
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
