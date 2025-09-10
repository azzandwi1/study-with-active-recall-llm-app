"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Brain, ArrowLeft, FileText, LinkIcon, Type, Upload } from "lucide-react"
import Link from "next/link"
import { motion } from "framer-motion"
import { ApiKeyGate } from "@/components/api-key-gate"
import { FileDropZone } from "@/components/file-drop-zone"
import { URLInput } from "@/components/url-input"
import { TextInput } from "@/components/text-input"
import { ProgressIndicator } from "@/components/progress-indicator"
import { ResultsSummary } from "@/components/results-summary"
import { useToast } from "@/hooks/use-toast"
import { apiRequest } from "@/lib/api"

interface IngestResult {
  success: boolean
  extractedText: string
  wordCount: number
  flashcardsGenerated: number
  processingTime: number
}

export default function IngestPage() {
  const [activeTab, setActiveTab] = useState("pdf")
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [currentStep, setCurrentStep] = useState("")
  const [result, setResult] = useState<IngestResult | null>(null)
  const { toast } = useToast()

  const handleIngest = async (data: { type: "pdf" | "url" | "text"; content: File | string }) => {
    setIsProcessing(true)
    setProgress(0)
    setResult(null)

    try {
      // Step 1: Upload/Extract content
      setCurrentStep("Mengekstrak konten...")
      setProgress(25)

      const formData = new FormData()

      if (data.type === "pdf" && data.content instanceof File) {
        formData.append("file", data.content)
        formData.append("type", "pdf")
      } else {
        formData.append("content", data.content as string)
        formData.append("type", data.type)
      }

      const extractResponse = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"}/api/v1/ingest`,
        {
          method: "POST",
          headers: {
            "X-User-Gemini-Key": localStorage.getItem("gemini_api_key") || "",
          },
          body: formData,
        },
      )

      if (!extractResponse.ok) {
        throw new Error("Gagal mengekstrak konten")
      }

      const extractResult = await extractResponse.json()

      // Step 2: Generate flashcards
      setCurrentStep("Membuat flashcard...")
      setProgress(60)

      if (!extractResult.collection_id) {
        throw new Error("Gagal mendapatkan ID koleksi dari server")
      }

      // Store the collection ID for use in the learn page
      localStorage.setItem('latest_collection_id', extractResult.collection_id)

      const flashcardsResponse = await apiRequest("/api/v1/generate/flashcards", {
        method: "POST",
        body: JSON.stringify({
          collection_id: extractResult.collection_id,
          n_cards: 5,
          style: "basic",
        }),
      })

      // Step 3: Complete
      setCurrentStep("Menyelesaikan...")
      setProgress(100)

      setResult({
        success: true,
        extractedText: extractResult.extractedText,
        wordCount: extractResult.wordCount || 0,
        flashcardsGenerated: flashcardsResponse.flashcards?.length || 0,
        processingTime: Date.now() - Date.now(), // This would be calculated properly
      })

      toast({
        title: "Berhasil!",
        description: `${flashcardsResponse.flashcards?.length || 0} flashcard telah dibuat`,
      })
    } catch (error) {
      console.error("Ingest error:", error)
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Terjadi kesalahan saat memproses konten",
        variant: "destructive",
      })
    } finally {
      setIsProcessing(false)
      setCurrentStep("")
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted">
      {/* Header */}
      <header className="container mx-auto px-4 py-6">
        <nav className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/">
              <Button variant="ghost" size="sm" className="gap-2">
                <ArrowLeft className="h-4 w-4" />
                Kembali
              </Button>
            </Link>
            <div className="flex items-center gap-2">
              <Brain className="h-8 w-8 text-primary" />
              <span className="text-2xl font-bold text-foreground">Active Recall</span>
            </div>
          </div>
          <Link href="/settings">
            <Button variant="outline" size="sm">
              Pengaturan
            </Button>
          </Link>
        </nav>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-4xl">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-2">Unggah Materi Belajar</h1>
            <p className="text-muted-foreground">Pilih cara untuk menambahkan konten yang ingin Anda pelajari</p>
          </div>

          <ApiKeyGate>
            <div className="space-y-8">
              {/* Upload Tabs */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 }}
              >
                <Card className="rounded-2xl border-0 shadow-lg">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Upload className="h-5 w-5 text-primary" />
                      Pilih Sumber Konten
                    </CardTitle>
                    <CardDescription>Upload file PDF, masukkan URL artikel, atau ketik teks langsung</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                      <TabsList className="grid w-full grid-cols-3 rounded-xl">
                        <TabsTrigger value="pdf" className="gap-2 rounded-lg">
                          <FileText className="h-4 w-4" />
                          PDF
                        </TabsTrigger>
                        <TabsTrigger value="url" className="gap-2 rounded-lg">
                          <LinkIcon className="h-4 w-4" />
                          URL
                        </TabsTrigger>
                        <TabsTrigger value="text" className="gap-2 rounded-lg">
                          <Type className="h-4 w-4" />
                          Teks
                        </TabsTrigger>
                      </TabsList>

                      <TabsContent value="pdf" className="mt-6">
                        <FileDropZone onFileSelect={(file) => handleIngest({ type: "pdf", content: file })} />
                      </TabsContent>

                      <TabsContent value="url" className="mt-6">
                        <URLInput onSubmit={(url) => handleIngest({ type: "url", content: url })} />
                      </TabsContent>

                      <TabsContent value="text" className="mt-6">
                        <TextInput onSubmit={(text) => handleIngest({ type: "text", content: text })} />
                      </TabsContent>
                    </Tabs>
                  </CardContent>
                </Card>
              </motion.div>

              {/* Progress Indicator */}
              {isProcessing && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4 }}
                >
                  <ProgressIndicator progress={progress} currentStep={currentStep} />
                </motion.div>
              )}

              {/* Results Summary */}
              {result && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6 }}
                >
                  <ResultsSummary result={result} />
                </motion.div>
              )}
            </div>
          </ApiKeyGate>
        </motion.div>
      </main>
    </div>
  )
}
