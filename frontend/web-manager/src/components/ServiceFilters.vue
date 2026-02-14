<template>
  <div class="service-filters">
    <div class="filters-container">
      <button
        v-for="category in categories"
        :key="category.value"
        @click="selectCategory(category.value)"
        :class="[
          'filter-button',
          { 'active': modelValue === category.value }
        ]"
        :style="{ color: category.color }"
      >
        {{ category.label }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineEmits, defineProps } from 'vue'

interface Category {
  value: string
  label: string
  color: string
}

interface Props {
  modelValue: string
  categories: Category[]
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue'])

function selectCategory(value: string) {
  emit('update:modelValue', value)
}
</script>

<style scoped>
.service-filters {
  display: flex;
  justify-content: center;
  margin-bottom: 1rem;
}

.filters-container {
  display: flex;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.25rem;
  gap: 0.125rem;
}

.filter-button {
  padding: 0.5rem 1rem;
  background: transparent;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  color: #64748b;
}

.filter-button:hover {
  background: rgba(0, 0, 0, 0.05);
}

.filter-button.active {
  background: white;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  font-weight: 600;
}

@media (max-width: 768px) {
  .filters-container {
    flex-wrap: wrap;
    justify-content: center;
  }
}
</style>