"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Brain, Key, Shield, ArrowLeft, Save, Eye, EyeOff } from "lucide-react"
import Link from "next/link"
import { motion } from "framer-motion"
import { useToast } from "@/hooks/use-toast"

export default function SettingsPage() {
  const [apiKey, setApiKey] = useState("")
  const [privacyConsent, setPrivacyConsent] = useState(false)
  const [showApiKey, setShowApiKey] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    // Load existing API key and consent from localStorage
    const savedApiKey = localStorage.getItem("gemini_api_key")
    const savedConsent = localStorage.getItem("privacy_consent")

    if (savedApiKey) {
      setApiKey(savedApiKey)
    }
    if (savedConsent === "true") {
      setPrivacyConsent(true)
    }
  }, [])

  const handleSave = async () => {
    if (!apiKey.trim()) {
      toast({
        title: "Error",
        description: "Kunci API Gemini wajib diisi",
        variant: "destructive",
      })
      return
    }

    if (!privacyConsent) {
      toast({
        title: "Error",
        description: "Anda harus menyetujui kebijakan privasi",
        variant: "destructive",
      })
      return
    }

    setIsLoading(true)

    try {
      // Save to localStorage
      localStorage.setItem("gemini_api_key", apiKey.trim())
      localStorage.setItem("privacy_consent", "true")

      toast({
        title: "Berhasil",
        description: "Pengaturan telah disimpan",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Gagal menyimpan pengaturan",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleClearData = () => {
    localStorage.removeItem("gemini_api_key")
    localStorage.removeItem("privacy_consent")
    setApiKey("")
    setPrivacyConsent(false)

    toast({
      title: "Berhasil",
      description: "Data telah dihapus",
    })
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
        </nav>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-2xl">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-2">Pengaturan</h1>
            <p className="text-muted-foreground">Kelola kunci API dan preferensi aplikasi Anda</p>
          </div>

          {/* Privacy Notice */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="mb-8"
          >
            <Alert className="border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-950/20">
              <Shield className="h-4 w-4 text-amber-600" />
              <AlertDescription className="text-amber-800 dark:text-amber-200">
                <div className="space-y-2">
                  <h3 className="font-semibold">Peringatan Privasi Data</h3>
                  <p className="text-sm leading-relaxed">
                    Menggunakan Gemini API berarti prompt dan unggahan Anda mungkin digunakan oleh Google untuk
                    peningkatan model sesuai pengaturan akun/API Anda. Jangan kirim data sensitif.
                  </p>
                </div>
              </AlertDescription>
            </Alert>
          </motion.div>

          {/* API Key Configuration */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <Card className="rounded-2xl border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Key className="h-5 w-5 text-primary" />
                  Konfigurasi API
                </CardTitle>
                <CardDescription>
                  Masukkan kunci API Gemini Anda untuk menggunakan fitur AI dalam aplikasi
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="api-key">Kunci API Gemini *</Label>
                  <div className="relative">
                    <Input
                      id="api-key"
                      type={showApiKey ? "text" : "password"}
                      placeholder="Masukkan kunci API Gemini Anda..."
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      className="pr-10 rounded-xl"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                      onClick={() => setShowApiKey(!showApiKey)}
                    >
                      {showApiKey ? (
                        <EyeOff className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <Eye className="h-4 w-4 text-muted-foreground" />
                      )}
                    </Button>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Dapatkan kunci API Anda di{" "}
                    <a
                      href="https://makersuite.google.com/app/apikey"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                    >
                      Google AI Studio
                    </a>
                  </p>
                </div>

                {/* Privacy Consent */}
                <div className="space-y-4 p-4 bg-muted/50 rounded-xl">
                  <div className="flex items-start space-x-3">
                    <Checkbox
                      id="privacy-consent"
                      checked={privacyConsent}
                      onCheckedChange={(checked) => setPrivacyConsent(checked as boolean)}
                      className="mt-1"
                    />
                    <div className="space-y-1">
                      <Label htmlFor="privacy-consent" className="text-sm font-medium leading-relaxed cursor-pointer">
                        Saya paham dan menyetujui kebijakan privasi di atas *
                      </Label>
                      <p className="text-xs text-muted-foreground">
                        Persetujuan ini diperlukan untuk menggunakan fitur AI dalam aplikasi
                      </p>
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row gap-3 pt-4">
                  <Button
                    onClick={handleSave}
                    disabled={isLoading || !apiKey.trim() || !privacyConsent}
                    className="flex-1 rounded-xl gap-2"
                  >
                    <Save className="h-4 w-4" />
                    {isLoading ? "Menyimpan..." : "Simpan Pengaturan"}
                  </Button>

                  <Button variant="outline" onClick={handleClearData} className="flex-1 rounded-xl bg-transparent">
                    Hapus Data
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Additional Information */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="mt-8"
          >
            <Card className="rounded-2xl border-0 shadow-lg bg-card/50">
              <CardContent className="p-6">
                <h3 className="font-semibold mb-3 text-card-foreground">Informasi Keamanan</h3>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex items-start gap-2">
                    <div className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0" />
                    Kunci API disimpan secara lokal di browser Anda
                  </li>
                  <li className="flex items-start gap-2">
                    <div className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0" />
                    Data tidak dikirim ke server kami
                  </li>
                  <li className="flex items-start gap-2">
                    <div className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0" />
                    Anda dapat menghapus data kapan saja
                  </li>
                </ul>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>
      </main>
    </div>
  )
}
