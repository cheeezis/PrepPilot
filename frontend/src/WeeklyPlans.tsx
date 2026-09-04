import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { deleteWeeklyPlan, generateWeeklyPlan, listWeeklyPlans, WeeklyPlanApiError, type WeeklyPlan, type WeeklyPlanInput } from './api/weeklyPlans'

const emptyDraft = { start_date: '', snacks_per_day: '1', calories_target_kcal: '', protein_minimum_g: '', carbohydrates_target_g: '', fat_maximum_g: '' }

export function WeeklyPlans() {
  const [plans, setPlans] = useState<WeeklyPlan[]>([])
  const [draft, setDraft] = useState(emptyDraft)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    listWeeklyPlans(controller.signal).then(setPlans).catch((reason: unknown) => setError(message(reason))).finally(() => setLoading(false))
    return () => controller.abort()
  }, [])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setSaving(true); setError(null)
    const input = toInput(false)
    try {
      let plan: WeeklyPlan
      try { plan = await generateWeeklyPlan(input) } catch (reason) {
        if (!(reason instanceof WeeklyPlanApiError) || reason.message !== 'Für diesen Zeitraum existiert bereits ein Wochenplan' || !window.confirm('Für diesen Zeitraum existiert bereits ein Plan. Wirklich ersetzen?')) throw reason
        plan = await generateWeeklyPlan({ ...input, replace_existing: true })
      }
      setPlans((current) => [plan, ...current.filter((item) => item.start_date !== plan.start_date)])
    } catch (reason) { setError(message(reason)) } finally { setSaving(false) }
  }

  function toInput(replace_existing: boolean): WeeklyPlanInput {
    return { start_date: draft.start_date, snacks_per_day: Number(draft.snacks_per_day), calories_target_kcal: Number(draft.calories_target_kcal), protein_minimum_g: Number(draft.protein_minimum_g), carbohydrates_target_g: Number(draft.carbohydrates_target_g), fat_maximum_g: Number(draft.fat_maximum_g), replace_existing }
  }

  async function remove(plan: WeeklyPlan) {
    if (!window.confirm(`Wochenplan ab ${formatDate(plan.start_date)} löschen?`)) return
    try { await deleteWeeklyPlan(plan.id); setPlans((current) => current.filter((item) => item.id !== plan.id)) } catch (reason) { setError(message(reason)) }
  }

  return <section className="plan-layout">
    <form className="food-form plan-form" onSubmit={submit}>
      <div className="section-heading"><p className="eyebrow">Neue Woche</p><h2>Wochenplan erzeugen</h2></div>
      <label className="field field--wide"><span>Startdatum</span><input required type="date" value={draft.start_date} onChange={(event) => setDraft({ ...draft, start_date: event.target.value })} /></label>
      <label className="field field--wide"><span>Snacks pro Tag</span><select value={draft.snacks_per_day} onChange={(event) => setDraft({ ...draft, snacks_per_day: event.target.value })}>{[0,1,2,3].map((value) => <option value={value} key={value}>{value}</option>)}</select></label>
      <TargetField label="Kalorienziel" unit="kcal" value={draft.calories_target_kcal} onChange={(value) => setDraft({ ...draft, calories_target_kcal: value })} />
      <TargetField label="Proteinminimum" unit="g" value={draft.protein_minimum_g} onChange={(value) => setDraft({ ...draft, protein_minimum_g: value })} />
      <TargetField label="Kohlenhydratziel" unit="g" value={draft.carbohydrates_target_g} onChange={(value) => setDraft({ ...draft, carbohydrates_target_g: value })} />
      <TargetField label="Fettmaximum" unit="g" value={draft.fat_maximum_g} onChange={(value) => setDraft({ ...draft, fat_maximum_g: value })} />
      <div className="form-actions"><button disabled={saving} type="submit">{saving ? 'Plan wird erzeugt …' : 'Plan erzeugen'}</button></div>
    </form>
    <section className="food-catalog"><div className="catalog-heading"><div><p className="eyebrow">Gespeicherte Historie</p><h2>Wochenpläne</h2></div><span>{plans.length}</span></div>{error && <p className="notice notice--error">{error}</p>}{loading ? <p className="notice">Wochenpläne werden geladen …</p> : plans.length === 0 ? <div className="empty-state"><div className="empty-state__icon">7</div><div><h3>Noch kein Wochenplan</h3><p>Lege links den ersten Zeitraum und deine täglichen Ziele fest.</p></div></div> : <div className="plan-list">{plans.map((plan) => <PlanCard plan={plan} onDelete={() => void remove(plan)} key={plan.id} />)}</div>}</section>
  </section>
}

function TargetField({ label, unit, value, onChange }: { label: string; unit: string; value: string; onChange: (value: string) => void }) {
  return <label className="field"><span>{label}</span><div className="number-input"><input required type="number" min="0" step="0.01" value={value} onChange={(event) => onChange(event.target.value)} /><small>{unit}</small></div></label>
}

function PlanCard({ plan, onDelete }: { plan: WeeklyPlan; onDelete: () => void }) {
  const days = Array.from({ length: 7 }, (_, day) => plan.assignments.filter((item) => item.day_index === day))
  return <details className="plan-card"><summary><span>{formatDate(plan.start_date)}–{formatDate(plan.end_date)}</span><span>{plan.snacks_per_day} Snacks/Tag</span></summary><div className="plan-targets">{plan.calories_target_kcal} kcal · mindestens {plan.protein_minimum_g} g Protein · {plan.carbohydrates_target_g} g Kohlenhydrate · höchstens {plan.fat_maximum_g} g Fett</div><div className="plan-days">{days.map((assignments, day) => <section key={day}><h3>{formatDate(assignments[0]?.date ?? plan.start_date)}</h3>{assignments.map((item) => <p key={item.id}><span>{roleLabel(item.meal_role, item.slot_number)}</span><strong>{item.recipe_title}</strong>{item.portion_number && <small>Portion {item.portion_number}/{item.recipe_servings}</small>}</p>)}</section>)}</div><button type="button" className="button-danger" onClick={onDelete}>Wochenplan löschen</button></details>
}

function roleLabel(role: string, slot: number) { return role === 'breakfast' ? 'Frühstück' : role === 'lunch' ? 'Mittagessen' : role === 'dinner' ? 'Abendessen' : `Snack ${slot}` }
function formatDate(value: string) { return new Intl.DateTimeFormat('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${value}T00:00:00Z`)) }
function message(reason: unknown) { return reason instanceof Error ? reason.message : 'Ein unbekannter Fehler ist aufgetreten' }
